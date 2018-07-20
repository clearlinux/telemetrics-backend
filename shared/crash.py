#
# Copyright 2015-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
from operator import itemgetter
from collections import namedtuple
import subprocess
import re
from .model import Record, GuiltyBlacklist
from . import app

try:
    from uwsgidecorators import spool
except ImportError:
    def spool(f):
        f.spool = f
        return f

filters = []

# Groups for the frame_pattern below
# 1 - frame number + one space
# 2 - function name + optional arguments
# 3 - rest of the line
# 4 - module name (inside the [])
# 5 - optional frame source file and line number info

# TODO: The current c++filt logic depends on properly subsituting c++filt
# output for the function name. Thus, it is very, very important to keep a
# capture group that extends from the function name to the end of the frame as
# long as this logic remains the same. Probably better to rework the code to
# *not* destructively overwrite the backtrace field. Maybe store the filtered
# output in a different field.

frame_pattern = "^(#\d+ )(.+)( - \[(.*)\](.*))$"

backtrace_classes = [
    'org.clearlinux/crash/clr',
    'org.clearlinux/kernel/bug',
    'org.clearlinux/kernel/stackoverflow',
    'org.clearlinux/kernel/warning'
]

other_classes = [
    'org.clearlinux/crash/unknown',
    'org.clearlinux/crash/clr-build',
    'org.clearlinux/crash/error'
]


def get_all_classes():
    return backtrace_classes + other_classes


def get_backtrace_classes():
    return backtrace_classes


def get_other_classes():
    return other_classes


def is_crash_classification(klass):
    return (klass in backtrace_classes) and True or False


def is_blacklisted(function, module):
    funcmod = (function, module)
    if funcmod in filters:
        return True

    return False


def demangle_backtrace(bt):
    new_bt = []
    prog = '/usr/bin/c++filt'

    frame_regex = re.compile(frame_pattern)
    lines = bt.splitlines()

    for line in lines:
        m = frame_regex.match(line)
        if m:
            func = m.group(2)

            # A frame with missing symbols is a special case, so skip it
            if func == '???':
                new_bt.append(line)
                continue

            # FIXME: this logic will break once the crash probe starts sending
            # function argument values; make this more generic!
            if func[-2:] == '()':
                # The crash probe adds the () to the function name, but c++filt
                # cannot demangle a symbol with the () suffix
                func_name = func[:-2]
            else:
                # Assume already demangled, or this is from a kernel crash record
                new_bt.append(line)
                continue

            try:
                new_func = subprocess.check_output([prog, func_name], universal_newlines=True)
            except:
                new_bt.append(line)
                continue

            # c++filt adds a trailing newline to the output
            new_func = new_func.rstrip()

            # Restore () if this was not a mangled symbol
            if new_func == func_name:
                new_func = func_name + '()'

            repl_str = r'\1{}\3'.format(new_func)
            new_line = frame_regex.sub(repl_str, line)
            new_bt.append(new_line)
        else:
            new_bt.append(line)

    return '\n'.join(new_bt)


def find_guilty(backtrace):
    frame_regex = re.compile(frame_pattern)

    guilty = {}

    lines = backtrace.splitlines()

    first_unknown = None
    in_backtrace = False
    prev_frame = None
    found_match = False
    found_unknown = False

    # Begin guilty detection process
    for line in lines[1:]:
        m = frame_regex.match(line)

        if m:
            # Either this is the first frame of the backtrace, or we are still
            # iterating through the backtrace.
            in_backtrace = True

            func = m.group(2)
            mod = m.group(4)

            # Only consider blacklisted function/module pairs as a last resort.
            # It's likely that the blacklisted pairs will never be chosen as
            # worthy candidates... if they are, the guilty blacklist may be
            # filtering too much.
            if is_blacklisted(func, mod):
                prev_frame = (func, mod)
                continue

            # Consider the first frame without function symbols ('???') only if
            # there are no function symbols for any frames lower in the stack.
            if (func == '???' or func[:2] == '? ') and not found_unknown:
                found_unknown = True
                first_unknown = (func, mod)
                prev_frame = (func, mod)
                continue
            elif func == '???':
                # In this case, we've already encountered a frame with missing
                # function symbols, so skip it, but save the info for backup.
                prev_frame = (func, mod)
                continue

            # If the previous three conditional checks fail, then we have found
            # the best guilty candidate: it is not in the blacklist, and it has
            # function symbols.
            guilty['function'] = func
            guilty['module'] = mod
            guilty['count'] = 1

            found_match = True
            return (guilty, found_match)

        elif in_backtrace:
            # We have processed the entire backtrace for the crashing thread of
            # the process, but no solid guilty has been found. Since we only
            # consider the crashing thread for guilty detection, stop iterating
            # through the remainder of the threads at this point.
            break

    # Implement a backup plan to ensure that a guilty is chosen.
    if found_unknown:
        # Take preference for '???'
        guilty['function'] = first_unknown[0]
        guilty['module'] = first_unknown[1]
        guilty['count'] = 1
        found_match = True
    elif prev_frame:
        # Choose the previous frame as a last resort
        guilty['function'] = prev_frame[0]
        guilty['module'] = prev_frame[1]
        guilty['count'] = 1
        found_match = True

    return (guilty, found_match)


def _process_guilties(args):
    if isinstance(args['klass'], bytes):
        klass = args['klass'].decode()
    else:
        klass = args['klass']
    # In case the caller does not check for proper classification, bail early
    if not is_crash_classification(klass):
        return
    if 'id' in args:
        record_id = int(args['id'])
    else:
        record_id = None
    global filters
    with app.app_context():
        crashes = Record.get_new_crash_records(classes=get_backtrace_classes(), id=record_id)
        filters = GuiltyBlacklist.get_guilties()
        for rec in crashes:
            if rec.payload:
                new_bt = demangle_backtrace(rec.payload)
                rec.payload = new_bt
                # TODO: update the rec.payload field as well
                Record.commit_guilty_changes()
                g, match = find_guilty(rec.payload)
                if match:
                    function = g['function']
                    module = g['module']
                    db_guilty = Record.get_guilty_for_funcmod(function, module)
                    if db_guilty is None:
                        db_guilty = Record.init_guilty(function, module)
                    Record.create_guilty_for_record(rec, db_guilty)
                    Record.set_processed_flag(rec)

        Record.commit_guilty_changes()


@spool
def process_guilties(args):
    _process_guilties(args)


def process_guilties_sync(**args):
    _process_guilties(args)


def guilty_list_per_build(guilties):
    # TODO: should compute max values per build with a subquery instead
    build_maxcount = {}

    buildset = set()
    buildlist = []
    newlist = []

    for g in guilties:
        found_entry = False
        guilty_str = g[0] + ' - [' + g[1] + ']'
        build, count, guilty_id, comment = (g[2], g[3], g[4], g[5])
        for i, n in enumerate(newlist):
            if guilty_str == n['guilty']:
                newlist[i]['total'] += count
                newlist[i]['builds'].append((build, count))
                if build in build_maxcount:
                    build_maxcount[build] = max(build_maxcount[build], count)
                else:
                    build_maxcount[build] = count
                found_entry = True
                break

        if found_entry:
            continue

        entry = {}
        entry['guilty'] = guilty_str
        entry['total'] = count
        entry['guilty_id'] = guilty_id
        entry['comment'] = comment
        entry['builds'] = []
        entry['builds'].append((build, count))
        if build in build_maxcount:
            build_maxcount[build] = max(build_maxcount[build], count)
        else:
            build_maxcount[build] = count
        newlist.append(entry)

    # We only care about the top 10 guilties
    newlist = sorted(newlist, key=itemgetter('total'), reverse=True)[:10]
    for guilty in newlist:
        for build in guilty['builds']:
            buildset.add(build[0])

    buildlist = list(buildset)
    buildlist = sorted(buildlist, key=lambda b: int(b[0]), reverse=True)

    # For crashes not occuring in a particular build, provide a "0" value for
    # the count. This simplifies table generation in the jinja template.
    for i, g in enumerate(newlist):
        builds, counts = list(zip(*g['builds']))
        counter = 0
        for b in buildlist:
            if b not in builds:
                newlist[i]['builds'].insert(counter, (b, "0"))
            counter += 1

    for i, b in enumerate(buildlist):
        buildlist[i] = (b, build_maxcount[b])

    buildlist = sorted(buildlist, key=lambda b: int(b[0]), reverse=True)

    for i, b in enumerate(newlist):
        newlist[i]['builds'] = sorted(newlist[i]['builds'], key=lambda b: int(b[0]), reverse=True)

    return (buildlist, newlist)


def guilty_list_for_build(guilties, filter='overall'):
    newlist = []

    for g in guilties:
        found_entry = False
        guilty_str = g[0] + ' - [' + g[1] + ']'
        build, count, guilty_id, comment = (g[2], g[3], g[4], g[5])
        for i, n in enumerate(newlist):
            if guilty_str == n['guilty'] and filter in ['overall', build]:
                newlist[i]['total'] += count
                found_entry = True
                break

        if found_entry:
            continue

        if filter in ['overall', build]:
            entry = {}
            entry['guilty'] = guilty_str
            entry['total'] = count
            entry['guilty_id'] = guilty_id
            entry['comment'] = comment
            newlist.append(entry)

    # We only care about the top 10 guilties
    newlist = sorted(newlist, key=itemgetter('total'), reverse=True)[:10]

    return newlist


def get_all_funcmods():
    frame_regex = re.compile(frame_pattern)
    funcmodset = set()
    funcmodlist = []
    backtraces = Record.get_crash_backtraces(classes=get_backtrace_classes())

    for b in backtraces:
        lines = b[0].splitlines()
        for line in lines:
            match = frame_regex.match(line)
            if match:
                funcmodset.add((match.group(2), match.group(4)))

    return sorted(funcmodset)


def parse_backtrace(backtrace):
    program_regex = re.compile('^Process: (.*)$')
    pid_regex = re.compile('^PID: ([0-9]+)$')
    signal_regex = re.compile('^Signal: ([0-9]+)$')
    bt_header_regex = re.compile('^Backtrace \(TID ([0-9]+)\):$')
    frame_regex = re.compile(frame_pattern)

    Crash = namedtuple('Crash', ['record_id', 'program', 'pid', 'signal', 'backtrace'])
    program = ''
    pid = ''
    signal = ''
    frames = []
    parsed_header = False

    lines = backtrace[0].splitlines()
    for line in lines:
        # Header info
        match = program_regex.match(line)
        if match:
            program = match.group(1)
            continue
        match = pid_regex.match(line)
        if match:
            pid = match.group(1)
            continue
        match = signal_regex.match(line)
        if match:
            signal = match.group(1)
            continue

        # We only care about the backtrace from the crashing thread, which
        # is listed first in the payload.
        match = bt_header_regex.match(line)
        if match and not parsed_header:
            parsed_header = True
        elif match:
            break

        match = frame_regex.match(line)
        if match:
            frames.append((match.group(2), match.group(4), match.group(5)))

    # Populate a namedtuple for convenience
    record_id = backtrace[1]
    c = Crash(record_id, program, pid, signal, frames)
    return c


def explode_backtraces(classes=None, guilty_id=None, machine_id=None, build=None):
    crashes = []
    backtraces = Record.get_crash_backtraces(classes, guilty_id, machine_id, build)
    for b in backtraces:
        crashes.append(parse_backtrace(b))
    return crashes


# vi: ts=4 et sw=4 sts=4

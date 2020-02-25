""" Crash processing logic """
# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections import namedtuple
import re
import cxxfilt

# Groups for the FRAME_PATTERN below
# 1 - frame number + one space
# 2 - function name + optional arguments
# 3 - rest of the line
# 4 - module name (inside the [])
# 5 - optional frame source file and line number info

GUILTY_BLACKLIST = None

FRAME_PATTERN = r'^(#\d+ )(.+)( - \[(.*)\](.*))$'

BACKTRACE_CLASSES = [
    'org.clearlinux/crash/clr',
    'org.clearlinux/kernel/bug',
    'org.clearlinux/kernel/stackoverflow',
    'org.clearlinux/kernel/warning'
]

OTHER_CLASSES = [
    'org.clearlinux/crash/unknown',
    'org.clearlinux/crash/clr-build',
    'org.clearlinux/crash/error'
]

def get_all_classes():
    """
    Returns a list of classes that contain
    payload for crashes.
    """
    return BACKTRACE_CLASSES + OTHER_CLASSES


def get_backtrace_classes():
    """
    Returns a list of classes that contain
    payloads with a crash backtrace.
    """
    return BACKTRACE_CLASSES


def demangle_backtrace(backtrace):
    """
    Returns a demangled backtrace.
    Args:
      * backtrace, a backtrace to demangle
    """
    new_bt = []

    frame_regex = re.compile(FRAME_PATTERN)
    lines = backtrace.splitlines()

    for line in lines:
        frame = frame_regex.match(line)
        if frame:
            func = frame.group(2)

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
                new_func = cxxfilt.demangle(func_name)
            except cxxfilt.InvalidName:
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
    """
    Returns a guilty function found in the backtrace.
    Args:
       * backtrace, the backtrace to search for guilty function
    """
    frame_regex = re.compile(FRAME_PATTERN)

    guilty = {}

    lines = backtrace.splitlines()

    first_unknown = None
    in_backtrace = False
    prev_frame = None
    found_match = False
    found_unknown = False

    # Begin guilty detection process
    for line in lines[1:]:
        frame = frame_regex.match(line)

        if frame:
            # Either this is the first frame of the backtrace, or we are still
            # iterating through the backtrace.
            in_backtrace = True

            func = frame.group(2)
            mod = frame.group(4)

            # Only consider blacklisted function/module pairs as a last resort.
            # It's likely that the blacklisted pairs will never be chosen as
            # worthy candidates... if they are, the guilty blacklist may be
            # filtering too much.
            if GUILTY_BLACKLIST.contains((func, mod)):
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


def parse_crash(backtrace):
    """
    Returns function, module tuple from a crash
    Args:
       * backtrace, backtrace to extract crash.
    """
    guilty, match = find_guilty(backtrace)
    if match:
        function = guilty['function']
        module = guilty['module']
        return function, module
    return None, None


def parse_backtrace(backtrace):
    """
    Returns a parsed backtraces
    Args:
       * bactrace, a crash backtrace
    """
    program_regex = re.compile(r'^Process: (.*)$')
    pid_regex = re.compile(r'^PID: ([0-9]+)$')
    signal_regex = re.compile(r'^Signal: ([0-9]+)$')
    bt_header_regex = re.compile(r'^Backtrace \(TID ([0-9]+)\):$')
    frame_regex = re.compile(FRAME_PATTERN)

    crash = namedtuple('Crash', ['record_id', 'program', 'pid', 'signal', 'backtrace'])
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
    return crash(record_id, program, pid, signal, frames)

# vi: ts=4 et sw=4 sts=4

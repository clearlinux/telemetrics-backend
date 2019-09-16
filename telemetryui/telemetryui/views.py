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

import ast
import re
import time
import json
import datetime
import importlib
from flask import (
    render_template,
    request,
    session,
    Blueprint)
from flask import (
    url_for,
    redirect,
    flash,
    abort)
from . import (
    app,
    crash,
    forms)
from .model import (
    Record,
    Guilty,
    GuiltyBlacklist)
from .updates import compute_update_matrix
from flask import Response
import redis

RECORDS_PER_PAGE = app.config.get('RECORDS_PER_PAGE', 50)
MAX_RECORDS_PER_PAGE = app.config.get('MAX_RECORDS_PER_PAGE', 1000)

@app.route('/telemetryui/', methods=['GET', 'POST'])
@app.route('/telemetryui/records', methods=['GET', 'POST'])
@app.route('/telemetryui/records/<int:page>', methods=['GET', 'POST'])
def records(page=1):
    form = forms.RecordFilterForm()

    class_strings = get_cached_data("class_strings", 600, Record.get_classifications, with_regex=True)
    builds = get_cached_data("builds", 600, Record.get_builds)
    os_map = get_cached_data("os_map", 600, Record.get_os_map)

    form.classification.choices = [(cs, cs) if "*" not in cs else (cs.replace("*", "%"), cs) for cs in class_strings]
    form.classification.choices.insert(0, ("All", "All"))
    form.build.choices = [(b[0], b[0]) for b in builds]
    form.build.choices.insert(0, ("All", "All"))

    form.severity.choices = [("All", "All"), ("1", "1 - low"), ("2", "2 - med"), ("3", "3 - high"), ("4", "4 - crit")]
    cl = session.get('severity')

    form.system_name.choices = [("All", "All")] + [(n, n) for n in os_map.keys()]

    form.machine_id.default = ""

    form.data_source.choices = [("All", "All")] + [('external', 'External'), ('internal', 'Internal')]

    if request.method == 'POST':
        if form.validate_on_submit() is False:
            print("Was not able to validate fields")
            for error in form.build.errors:
                print(error)
            for error in form.classification.errors:
                print(error)
            for error in form.severity.errors:
                print(error)
            out_records = Record.query.order_by(Record.id.desc()).paginate(page, RECORDS_PER_PAGE, False)
            return render_template('records.html', records=out_records, form=form)
        else:
            classification = request.form.get('classification')
            system_name = request.form.get('system_name')
            build = request.form.get('build')
            severity = request.form.get('severity')
            page_size = request.form.get('page_size')
            machine_id = request.form.get('machine_id')
            payload = request.form.get('payload')
            not_payload = request.form.get('not_payload')
            from_date = request.form.get('from_date')
            to_date = request.form.get('to_date')
            data_source = request.form.get('data_source')

            redirect_args = {
                "page_size": page_size if page_size != "" else None,
                "system_name": system_name if system_name != "All" else None,
                "build": build if build != "All" else None,
                "severity": severity if severity != "All" else None,
                "classification": classification if classification != "All" else None,
                "machine_id": machine_id if machine_id != "" else None,
                "payload": payload if payload != "" else None,
                "not_payload": not_payload if not_payload != "" else None,
                "from_date": from_date if from_date != "" else None,
                "to_date": to_date if to_date != "" else None,
                "data_source": data_source if data_source != "All" else None,
            }
            dest = 'records'

            if 'csv_inline' in request.form:
                redirect_args['format_type'] = 'inline'
                redirect_args['timestamp'] = time.time()
                dest = 'export_csv'
            elif 'csv_attachment' in request.form:
                redirect_args['format_type'] = 'attach'
                redirect_args['timestamp'] = time.time()
                dest = 'export_csv'

            redirect_args['page'] = 1
            url = url_for(dest, **redirect_args)
            return redirect(url)

    elif request.method == 'GET':
        classification = request.args.get('classification')
        system_name = request.args.get('system_name')
        build = request.args.get('build')
        severity = request.args.get('severity')
        page_size = request.args.get('page_size')
        machine_id = request.args.get('machine_id')
        payload = request.args.get('payload')
        not_payload = request.args.get('not_payload')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        data_source = request.args.get('data_source')

        if classification is not None:
            form.classification.default = classification
        if build is not None:
            form.build.default = build
        if system_name is not None:
            form.system_name.default = system_name
        if severity is not None:
            form.severity.default = severity
        if machine_id is not None:
            form.machine_id.default = machine_id
        if payload is not None:
            form.payload.default = payload
        if not_payload is not None:
            form.not_payload.default = not_payload
        if from_date is not None:
            form.from_date.default = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        if to_date is not None:
            form.to_date.default = datetime.datetime.strptime(to_date, "%Y-%m-%d")
        if data_source is not None:
            form.data_source.default = data_source

        form.process()

        if page_size is None:
            page_size = RECORDS_PER_PAGE
        elif int(page_size) > MAX_RECORDS_PER_PAGE:
            page_size = MAX_RECORDS_PER_PAGE
        out_records = Record.filter_records(build, classification, severity, machine_id, system_name=system_name,
                                            payload=payload, not_payload=not_payload, data_source=data_source,
                                            from_date=from_date, to_date=to_date).paginate(page, int(page_size), False)
        return render_template('records.html', records=out_records, form=form, os_map=json.dumps(os_map))


@app.route('/telemetryui/records/record_details/<int:record_id>')
def record_details(record_id):
    record = Record.get_record(record_id)
    if not record:
        abort(404)
    return render_template('record_details.html', record=record)


@app.route('/telemetryui/builds')
def builds():
    build_rec_pairs = get_cached_data("build_rec_pairs", 600, Record.get_recordcnts_by_build)
    return render_template('builds.html', build_stats=build_rec_pairs)


@app.route('/telemetryui/stats')
def stats():
    # Display records per classification and records per machine type for now
    class_rec_pairs = get_cached_data("class_rec_pairs", 600, Record.get_recordcnts_by_classification)

    machine_rec_pairs = get_cached_data("machine_rec_pairs", 600, Record.get_recordcnts_by_machine_type)

    charts = [{'column': 'Classification', 'record_stats': class_rec_pairs},
              {'column': 'Platform', 'record_stats': machine_rec_pairs}]
    return render_template('stats.html', charts=charts)


@app.route('/telemetryui/crashes', methods=['GET', 'POST'])
@app.route('/telemetryui/crashes/page/<int:page>', methods=['GET'])
@app.route('/telemetryui/crashes/<string:filter>', methods=['GET', 'POST'])
def crashes(filter=None, page=1):
    form = forms.GuiltyDetailsForm()
    guilties_key = "tmp_top_crash_guilties"
    if request.method == 'POST':
        if form.validate_on_submit() is False:
            for e in form.comment.errors:
                flash('Error in comment field: {}'.format(e), 'danger')
            for e in form.guilty_id.errors:
                flash('Error in guilty_id field: {}'.format(e), 'danger')
            for e in form.hidden.errors:
                flash('Error in hidden field: {}'.format(e), 'danger')
            if filter:
                endpoint = url_for('crashes_filter', filter=filter)
            else:
                endpoint = url_for('crashes')
            return redirect(endpoint)
        else:
            comment = request.form['comment']
            id = request.form['guilty_id']
            hidden = request.form['hidden']

            # 'None' is from jinja2 when a NULL value is queried
            if comment in ['', 'None']:
                comment = None

            if hidden == 'yes':
                Guilty.update_hidden(id, True)
            elif hidden == 'no':
                pass

            Guilty.update_comment(id, comment)
            if filter:
                endpoint = url_for('crashes_filter', filter=filter)
            else:
                endpoint = url_for('crashes')

            # Delete cached query when user updates a guilty with comment or hidden
            uncache_data(guilties_key)
            return redirect(endpoint)

    all_classes = crash.get_all_classes()
    backtrace_classes = crash.get_backtrace_classes()
    tmp = get_cached_data(guilties_key, 600, Record.get_top_crash_guilties, classes=backtrace_classes)

    if filter:
        guilties = crash.guilty_list_for_build(tmp, filter)
        return render_template('crashes_filter.html', guilties=guilties, build=filter, form=form, pages=0, page=0)
    else:
        pages, out_builds, guilties = crash.guilty_list_per_build(tmp, page=page)
        return render_template('crashes.html', guilties=guilties, builds=out_builds, form=form, pages=pages, page=page)


@app.route('/telemetryui/crashes/guilty_details/<int:id>')
def guilty_details(id):
    function = Guilty.get_function(id)
    if not function:
        abort(404)
    module = Guilty.get_module(id)
    hidden = Guilty.get_hidden_value(id)
    query = Record.get_machine_ids_for_guilty(id)
    return render_template('guilty_details.html', guilty_id=id, query=query, func=function, mod=module, hide=hidden)


@app.route('/telemetryui/crashes/guilty_details/<int:id>/backtraces')
def guilty_backtraces(id):
    machine_id = request.args.get('machine_id')
    build = request.args.get('build')
    if not machine_id:
        machine_id = None
    if not build:
        build = None
    func = Guilty.get_function(id)
    mod = Guilty.get_module(id)
    funcmod = re.escape("{} - [{}]".format(func, mod))
    backtrace_classes = crash.get_backtrace_classes()
    # TODO: should consolidate backtraces
    backtraces = crash.explode_backtraces(classes=backtrace_classes, guilty_id=id, machine_id=machine_id, build=build)
    # Display at most 50 entries for now, until we have backtrace grouping and pagination
    return render_template('guilty_backtraces.html', backtraces=backtraces[:50], func=func, mod=mod, funcmod=funcmod, guiltyid=id)


@app.route('/telemetryui/crashes/guilty_edit/', methods=['GET', 'POST'])
def guilty_edit():
    guilty_id = request.args.get('guilty_id')
    rec_id = request.args.get('record_id')
    if not rec_id:
        return render_template('guilty_edit.html')
    else:
        result = crash.parse_backtrace(Record.get_crash_backtraces(record_id=rec_id))
        blacklist = GuiltyBlacklist.get_guilties()
        filters = ["{} [{}]".format(g[0], g[1]) for g in blacklist]

        # For form population, we only care about the first two fields per
        # frame. Also, exclude frames that are *always* blacklisted.
        choices = []
        for f in result.backtrace:
            # This is always the bottommost frame in a backtrace from the crash
            # probe. It can never be guilty.
            if re.search('^_start()', f[0]):
                continue
            # Appears in every crash probe backtrace.
            if re.search('^__libc_start_main()', f[0]) and re.search('libc.so.6', f[1]):
                continue
            choices.append((f[0], f[1]))

        form = forms.GuiltyEditOneForm()
        form.frames.choices = [("{}||||{}".format(f[0], f[1]), "{} [{}]".format(f[0], f[1])) for f in choices]

        # set "checked" attribute for all frames that are guilty blacklisted
        form.frames.data = []
        for f in choices:
            if f in blacklist:
                form.frames.data.append("{}||||{}".format(f[0], f[1]))

        # pass escaped function/module pair to the template for highlighting
        func = Guilty.get_function(guilty_id)
        mod = Guilty.get_module(guilty_id)
        funcmod = re.escape("{}||||{}".format(func, mod))

        if request.method == 'POST':
            if form.validate_on_submit():
                post_data = []
                for f in request.form.getlist('frames'):
                    func, mod = f.split('||||')
                    post_data.append((func, mod))
                to_add = []
                to_remove = []
                for choice in choices:
                    if choice in post_data:
                        to_add.append(choice)
                    else:
                        to_remove.append(choice)

                GuiltyBlacklist.update(to_add, to_remove)
                backtrace_classes = crash.get_backtrace_classes()

                if 'apply' in request.form:
                    Record.reset_processed_records(classes=backtrace_classes, id=rec_id)
                    crash.process_guilties_sync(klass='org.clearlinux/crash/clr'.encode(), id=str(rec_id).encode())
                    new_guilty = Record.get_guilty_id_for_record(rec_id)
                    flash('Updated blacklist and reprocessed record. If the new chosen guilty is correct, click "Submit".', 'success')
                    return redirect(url_for('guilty_edit', guilty_id=new_guilty, record_id=rec_id))
                elif 'apply_submit' in request.form:
                    Record.reset_processed_records(classes=backtrace_classes)
                    crash.process_guilties(klass='org.clearlinux/crash/clr'.encode())
                    flash('Updated guilty blacklist. Guilties will be recalculated in the background for all crash records.', 'success')
                    return redirect(url_for('crashes'))
            else:
                print('Error occurred')
                for e in form.frames.errors:
                    print(e)
                return redirect(url_for('guilty_edit', record_id=rec_id))

        return render_template('guilty_edit_one.html', crash_info=result, record_id=rec_id, filters=filters, form=form, funcmod=funcmod)


@app.route('/telemetryui/crashes/guilty_edit/add', methods=['GET', 'POST'])
def guilty_add():
    form_add = forms.GuiltyAddForm()
    funcmods = crash.get_all_funcmods()
    form_add.funcmod.choices = [("{}||||{}".format(f[0], f[1]), "{} [{}]".format(f[0], f[1])) for f in funcmods]
    guilties = GuiltyBlacklist.get_guilties()
    filters = ["{} [{}]".format(g[0], g[1]) for g in guilties]
    if request.method == 'POST':
        if form_add.validate_on_submit():
            func, mod = request.form['funcmod'].split('||||')

            res = GuiltyBlacklist.exists(func, mod)
            if res:
                flash('Filter already exists for "{} [{}]". Try again.'.format(func, mod), 'warning')
            else:
                GuiltyBlacklist.add(func, mod)
                flash('Added guilty filter for "{} [{}]"'.format(func, mod), 'success')
            return redirect(url_for('guilty_add'))
        else:
            print('Error occurred')
            for e in form_add.funcmod.errors:
                print(e)
            return redirect(url_for('guilty_add'))

    return render_template('guilty_add.html', form=form_add, filters=filters)


@app.route('/telemetryui/crashes/guilty_edit/remove', methods=['GET', 'POST'])
def guilty_remove():
    form_remove = forms.GuiltyRemoveForm()
    guilties = GuiltyBlacklist.get_guilties()
    count = len(guilties)
    form_remove.funcmod.choices = [("{}:{}".format(g[0], g[1]), "{} [{}]".format(g[0], g[1])) for g in guilties]
    if request.method == 'POST':
        if form_remove.validate_on_submit():
            res = request.form['funcmod']
            res = res.split(':')
            func, mod = (res[0], res[1])
            GuiltyBlacklist.remove(func, mod)
            flash('Removed guilty filter "{} [{}]"'.format(func, mod), 'success')
            return redirect(url_for('guilty_remove'))
        else:
            print('Error occurred')
            for e in form_remove.funcmod.errors:
                print(e)
            return redirect(url_for('guilty_remove'))

    return render_template('guilty_remove.html', form=form_remove, count=count)


@app.route('/telemetryui/crashes/guilty_edit/hidden', methods=['GET', 'POST'])
def guilty_hidden():
    form_hidden = forms.GuiltyHiddenForm()
    guilties = Guilty.get_hidden_guilties()
    count = len(guilties)
    form_hidden.funcmod.choices = [("{}:{}:{}".format(g[0], g[1], g[2]), "{} [{}]".format(g[1], g[2])) for g in guilties]
    if request.method == 'POST':
        if form_hidden.validate_on_submit():
            res = request.form['funcmod']
            res = res.split(':')
            id, func, mod = (res[0], res[1], res[2])
            Guilty.update_hidden(id, False)
            flash('Guilty "{} [{}]" is no longer hidden'.format(func, mod), 'success')
            return redirect(url_for('guilty_hidden'))
        else:
            for e in form_hidden.funcmod.errors:
                flash(e, 'warning')
            return redirect(url_for('guilty_hidden'))

    return render_template('guilty_hidden.html', form=form_hidden, count=count)


@app.route('/telemetryui/crashes/guilty_edit/reset', methods=['GET', 'POST'])
def guilty_reset():
    form_reset = forms.GuiltyResetForm()
    if request.method == 'POST':
        if form_reset.validate_on_submit():
            res = request.form['confirm']
            if res == 'yes':
                backtrace_classes = crash.get_backtrace_classes()
                Record.reset_processed_records(classes=backtrace_classes)
                # must pass args as bytes to uwsgi under Python 3
                crash.process_guilties(klass='org.clearlinux/crash/clr'.encode())
                flash('Successfully triggered a guilty reset. Guilties will be recalculated in the background.', 'success')
                return redirect(url_for('guilty_edit'))
            else:
                flash('Unexpected confirm value: {}'.format(res), 'warning')
                return redirect(url_for('guilty_reset'))
        else:
            for e in form_reset.confirm.errors:
                flash(e, 'warning')
            return redirect(url_for('guilty_reset'))

    return render_template('guilty_reset.html', form=form_reset)


@app.route('/telemetryui/mce', methods=['GET', 'POST'])
def mce():
    mce_classes = [
        "org.clearlinux/mce/corrected",
        "org.clearlinux/mce/SRAO",
        "org.clearlinux/mce/SRAR",
        "org.clearlinux/mce/UCNA",
    ]
    records = Record.filter_records(None, mce_classes, None, from_date="{}-01-01".format(datetime.datetime.now().year)).all()
    top10 = []
    maxcnt = 0
    by_machine_id = {}
    by_builds = {}
    by_mce_status = {}
    week_rec_map = {}
    class_rec_map = {}
    for record in records:
        week = time.strftime("%U", time.localtime(int(record.timestamp_client)))
        week_rec_map.setdefault(record.classification, {}).setdefault(week, 0)
        week_rec_map[record.classification][week] += 1
        class_rec_map.setdefault(record.classification, 0)
        class_rec_map[record.classification] += 1
        by_machine_id.setdefault(record.machine_id, {"builds": {}, "recordscnt": 0})
        by_machine_id[record.machine_id]["builds"].setdefault(record.build, 0)
        by_machine_id[record.machine_id]["builds"][record.build] += 1
        by_machine_id[record.machine_id]["recordscnt"] += 1
        by_builds.setdefault(record.build, 0)
        by_builds[record.build] += 1
        status_match = re.search('STATUS.*([A-Fa-f0-9]{8}) MCGSTATUS', record.payload)
        if status_match:
            status = status_match.group(1)
            if status in by_mce_status:
                by_mce_status[status] += 1
            else:
                by_mce_status[status] = 1
    for machine_id in list(by_machine_id.keys()):
        builds_cnt = by_machine_id[machine_id]["builds"]
        maxcnt = max(list(builds_cnt.values()) + [maxcnt])
        top10.append({
            "machine_id": machine_id,
            "recordscnt": by_machine_id[machine_id]["recordscnt"],
            "builds": by_machine_id[machine_id]["builds"]
        })
    top10.sort(key=lambda x: x["recordscnt"], reverse=True)
    charts = [{'column': 'classification', 'record_stats': class_rec_map.items(), 'type': 'pie', 'width': 6},
              {'column': 'build', 'record_stats': sorted(by_builds.items(), key=lambda x: x[0]), 'type': 'column', 'width': 6},
              {'column': 'status', 'record_stats': sorted(by_mce_status.items(), key=lambda x: x[0]), 'type': 'column', 'width': 6}]
    return render_template('mce.html', charts=charts, top10=top10, builds=sorted(by_builds.keys()), maxcnt=maxcnt, fullmce=week_rec_map)


@app.route('/telemetryui/thermal', methods=['GET', 'POST'])
def thermal():
    current_year = time.strftime("%Y", time.gmtime(time.time()))
    current_week = time.strftime("%U", time.gmtime(time.time()))
    current_last_week = time.strftime("%U", time.strptime(current_year + "1231", "%Y%m%d"))
    from_date = time.strftime("%Y-%m-%d", time.localtime(time.mktime(time.strptime(current_year + current_week + "0", "%Y%U%w")) - 2419200))  # 2419200 = (604800 * 4)
    records = Record.filter_records(None, ["org.clearlinux/mce/thermal"], None, from_date=from_date).all()
    week_rec_map = {}
    year_start = time.mktime(time.strptime(current_year + "000", "%Y%U%w"))
    for r in records:
        if r.timestamp_client >= year_start:
            week = str(int((r.timestamp_client - year_start) / 604800) + ((r.timestamp_client - year_start) % 604800 > 0))
            if week in week_rec_map:
                week_rec_map[week] += 1
            else:
                week_rec_map[week] = 1
    weeks = sorted(week_rec_map.keys(), key=lambda x: int(x), reverse=True)
    thermal_chart = [["Thermal records"] + ["Week: " + x for x in weeks]]
    weekly_records = ["org.clearlinux/mce/thermal"]
    for week in weeks:
        weekly_records.append(week_rec_map[week])
    thermal_chart.append(weekly_records)
    thermal_chart = json.dumps(thermal_chart)
    return render_template('thermal.html', thermal_chart=thermal_chart)


@app.route('/telemetryui/updates')
def updates():
    updates = get_cached_data("updates_data", 600, Record.get_updates)
    return json.dumps(updates)


@app.route('/telemetryui/population')
def population():
    charts = [{'id': 'Overall', 'time': None, 'timestr': 'Overall'},
              {'id': 'TwoWeeks', 'time': 14, 'timestr': 'Past Two Weeks'},
              {'id': 'OneWeek', 'time': 7, 'timestr': 'Past Week'},
              {'id': 'OneDay', 'time': 1, 'timestr': 'Past Day'},
              {'id': 'ThreeDay', 'time': 3, 'timestr': 'Three Days'}]

    for c in charts:
        msgs = get_cached_data(c['id'], 600, Record.get_heartbeat_msgs, c['time'])
        c['stats'] = (len(msgs) > 0) and msgs or None

    return render_template('population.html', charts=charts)


@app.route('/telemetryui/records/export/records-<int:timestamp>.csv')
def export_csv(timestamp):
    severity = request.args.get('severity')
    classification = request.args.get('classification')
    build = request.args.get('build')
    machine_id = request.args.get('machine_id')
    payload = request.args.get('payload')
    not_payload = request.args.get('not_payload')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    format_type = request.args.get('format_type')

    if format_type == 'inline':
        # TODO:
        # - make the limit configurable?
        filter = Record.filter_records(severity=severity, classification=classification, build=build, machine_id=machine_id, limit=10000)
    elif format_type == 'attach':
        filter = Record.filter_records(build, classification, severity, machine_id, payload=payload, not_payload=not_payload, from_date=from_date, to_date=to_date)

    def dump_contents():
        yield 'id,external,server_timestamp,severity,classification,build,machine_id,payload\n'
        rows = filter.all()
        for row in rows:
            yield ','.join('"' + re.sub('"', '""', str(v)) + '"' for v in row.to_list()).encode('unicode-escape') + b'\n'

    if format_type == 'inline':
        return Response(dump_contents(), mimetype='text/plain')
    elif format_type == 'attach':
        response = Response(dump_contents(), mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=export-{}.csv'.format(timestamp)
        return response


def is_plugin_valid(plugin):
    tab_name = getattr(plugin, "TAB_NAME", None)
    init = getattr(plugin, "init", None)

    if None in [tab_name, init]:
        return False

    if callable(init) is not True:
        return False

    return True


def load_plugin(plugin_name):
    print("loading {}".format(plugin_name))
    plugin_module = importlib.import_module("telemetryui.plugins.{}.views".format(plugin_name))

    def register_bp(a_blueprint):
        app.register_blueprint(a_blueprint, url_prefix='/telemetryui/plugins')

    if is_plugin_valid(plugin_module) is True:
        plugin_module.init(register_bp)
    else:
        print("Plugin {} could not be loaded".format(plugin_name))


def load_plugins():
    plugins = app.config.get('PLUGINS', [])
    for plugin in plugins:
        load_plugin(plugin)


def get_cached_data(varname, expiration, funct, *args, **kwargs):
    try:
        # Default parameters are to run on localhost with port 6379
        redis_client = redis.StrictRedis(decode_responses=True);
        # Try to get data from redis first
        ret = redis_client.get(varname)
        if ret is not None:
            # Convert to original type if successful
            ret = ast.literal_eval(ret)
        else:
            # If nothing was found, query the database
            ret = funct(*args, **kwargs)
            # Convert to string representation and cache via redis
            redis_client.set(varname, repr(ret), ex=expiration)
    except redis.exceptions.ConnectionError as e:
        print("%s Redis probably isn't running?" % str(e))
        # If we can't connect to redis, just query directly
        ret = funct(*args, **kwargs)
    return ret

def uncache_data(varname):
    try:
        redis_client = redis.StrictRedis(decode_responses=True);
        redis_client.delete(varname)
    except redis.exceptions.ConnectionError as e:
        print("%s Redis probably isn't running?" % str(e))
    return

load_plugins()

# vi: ts=4 et sw=4 sts=4

# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from . import (
     crash,
     app,)
from .model import Record
from flask import (
     redirect,
     url_for,
     render_template)


RECORDS_PER_PAGE = app.config.get('RECORDS_PER_PAGE', 25)


def records_get(form, request, lastid=None):
    classification = request.args.get('classification')
    build = request.args.get('build')
    severity = request.args.get('severity')
    machine_id = request.args.get('machine_id')
    payload = request.args.get('payload')
    not_payload = request.args.get('not_payload')
    data_source = request.args.get('data_source')

    if classification is not None:
        form.classification.default = classification
    if build is not None:
        form.build.default = build
    if severity is not None:
        form.severity.default = severity
    if machine_id is not None:
        form.machine_id.default = machine_id
    if payload is not None:
        form.payload.default = payload
    if not_payload is not None:
        form.not_payload.default = not_payload
    if data_source is not None:
        form.data_source.default = data_source

    form.process()
    return Record.query_records(build, classification, severity, machine_id,
                                payload=payload, not_payload=not_payload,
                                data_source=data_source, from_id=lastid,
                                limit=RECORDS_PER_PAGE)


def records_post(form, request):

    if form.validate_on_submit() is False:
        out_records = Record.query.order_by(Record.id.desc()).limit(RECORDS_PER_PAGE).all()
        return render_template('records.html', records=out_records, form=form)
    else:
        classification = request.form.get('classification')
        system_name = request.form.get('system_name')
        build = request.form.get('build')
        severity = request.form.get('severity')
        machine_id = request.form.get('machine_id')
        payload = request.form.get('payload')
        not_payload = request.form.get('not_payload')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        data_source = request.form.get('data_source')

        redirect_args = { 
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
        dest = 'views_bp.records'

        if 'csv_attachment' in request.form:
            redirect_args['format_type'] = 'attach'
            redirect_args['timestamp'] = time.time()
            dest = 'views_bp.export_csv'

        url = url_for(dest, **redirect_args)
        return redirect(url)


def explode_backtraces(classes=None, guilty_id=None, machine_id=None, build=None):
    crashes = []
    backtraces = Record.get_crash_backtraces(classes, guilty_id, machine_id, build)
    for b in backtraces:
        crashes.append(crash.parse_backtrace(b))
    return crashes


# vi: ts=4 et sw=4 sts=4

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

import re
import time
import datetime
from flask import request
from flask import jsonify
from flask import redirect
from .model import (
    Classification,
    Build)
from .crash import (
    process_guilties,
    is_crash_classification)
from .purge import *

tm_version_regex = re.compile("^[0-9]+\.[0-9]+$")
client_id_regex = re.compile(
    "^[0-9]+[ \t]+[-/.:_+*a-zA-Z0-9]+[ \t]+[-/.:_+*a-zA-Z0-9]+$")
ts_v3_regex = re.compile("^[0-9]+$")
# FIXME: configurable limits
max_payload_len_inline = 30 * 1024	 # 30k
max_payload_len = 300 * 1024		 # 300k
POSTGRES_INT_MAX = 2147483647

# see config.py for the meaning of this value
TELEMETRY_ID = app.config.get("TELEMETRY_ID", "6907c830-eed9-4ce9-81ae-76daf8d88f0f")


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        app.logger.error("InvalidUsage ({}): {}".format(self.status_code, self.message))

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

    def __str__(self):
        return self.message


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.before_request
def before_request():
    headers = request.headers
    payload = request.data
    app.logger.info('\t'.join([
        datetime.datetime.today().ctime(),
        request.method,
        request.url,
        str(request.data),
        ', '.join([': '.join(x) for x in request.headers])])
    )


@app.route("/", methods=['GET', 'POST'])
@app.route("/v2/collector", methods=['GET', 'POST'])
def handler():
    if request.method == 'POST':
        tid_header = request.headers.get('X-Telemetry-TID')
        if not tid_header:
            raise InvalidUsage("Telemetry ID (TID) missing", 400)

        # The collector only accepts records with the configured TID value.
        # Make sure the TID in the collector config.py matches the TID
        # configured for telemetrics-client on the systems from which this
        # collector receives records.
        if tid_header != TELEMETRY_ID:
            err = "Telemetry ID mismatch. Expected: {}; Actual: {}".format(TELEMETRY_ID, tid_header)
            raise InvalidUsage(err, 400)

        record_format_version = request.headers.get('Record-Format-Version')
        if not record_format_version:
            raise InvalidUsage("Record format version missing", 400)

        severity = request.headers.get('Severity')
        if not severity:
            raise InvalidUsage("Severity missing", 400)

        classification = request.headers.get('Classification')
        if not classification:
            raise InvalidUsage("Classification missing", 400)

        machine_id = request.headers.get('Machine-Id')
        if not machine_id:
            raise InvalidUsage("Machine id missing", 400)

        if len(machine_id) > 32:
            raise InvalidUsage("Machine id too long", 400)

        timestamp = request.headers.get('Creation-Timestamp')
        if not timestamp:
            raise InvalidUsage("Timestamp missing", 400)

        ts_capture = int(timestamp)
        ts_reception = time.time()

        architecture = request.headers.get('Arch')
        if not architecture:
            raise InvalidUsage("Architecture missing", 400)

        host_type = request.headers.get('Host-Type')
        if not host_type:
            raise InvalidUsage("Host type missing", 400)

        kernel_version = request.headers.get('Kernel-Version')
        if not kernel_version:
            raise InvalidUsage("Kernel version missing", 400)

        os_name = request.headers.get('System-Name')
        if not os_name:
            raise InvalidUsage("OS name missing", 400)

        os_name = os_name.replace('"', '').replace("'", "")

        build = request.headers.get('Build')
        if not build:
            raise InvalidUsage("Build missing", 400)

        # It is common to see the build numbers quoted in os-release. We don't
        # need the quotes, so strip them from the semantic value.
        build = build.replace('"', '').replace("'", "")

        # The build number is stored as a string in the database, but if this
        # record is from a Clear Linux OS system, only accept an integer.
        # Otherwise, loosen the restriction to the characters listed for
        # VERSION_ID in os-release(5) in addition to the capital letters A-Z.
        if os_name == 'clear-linux-os':
            build_regex = re.compile(r"^[0-9]+$")
            if not build_regex.match(build):
                raise InvalidUsage("Clear Linux OS build version has invalid characters")
        else:
            build_regex = re.compile(r"^[-_a-zA-Z0-9.]+$")
            if not build_regex.match(build):
                raise InvalidUsage("Build version has invalid characters")

        payload_format_version = request.headers.get('Payload-Format-Version')
        if not payload_format_version:
            raise InvalidUsage("Payload format version missing", 400)
        if int(payload_format_version) > POSTGRES_INT_MAX:
            raise InvalidUsage("Payload format version outside of range supported")

        external = request.headers.get('X-CLR-External')
        if external and external == "true":
            external = True
        else:
            external = False

        try:
            # prefer UTF-8, if possible
            payload = request.data.decode('utf-8')
        except UnicodeError:
            # fallback to Latin-1, since it accepts all byte values
            payload = request.data.decode('latin-1')

        if classification == "org.clearlinux/mce/corrected" and "THERMAL" in payload:
            classification = "org.clearlinux/mce/thermal"

        db_class = Classification.query.filter_by(classification=classification).first()
        if db_class is None:
            db_class = Classification(classification)

        db_build = Build.query.filter_by(build=build).first()
        if db_build is None:
            db_build = Build(build)

        db_rec = Record.create(machine_id, host_type, severity, db_class, db_build, architecture, kernel_version,
                               record_format_version, ts_capture, ts_reception, payload_format_version, os_name,
                               external, payload)

        if is_crash_classification(classification):
            # must pass args as bytes to uwsgi under Python 3
            process_guilties(klass=classification.encode(), id=str(db_rec.id).encode())

        resp = jsonify(db_rec.to_dict())
        resp.status_code = 201
        return resp
    else:
        # print all the recorded messages so far
        return redirect("/telemetryui", code=302)


@app.route("/api/records", methods=['GET'])
def records_api_handler():
    '''
    query filters for simple query:
    classification
    severity
    build
    machine_id
    created_in_days - records created after given days
    created_in_sec - records created after given seconds

    TODO: Advanced query with pagination and following parameters?
    client_created_after - timestamp
    client_created_before - timestamp
    server_created_after - timestamp
    server_created_before - timestamp

    '''

    severity = request.args.get('severity')
    if severity and not severity.isdigit():
        raise InvalidUsage("Severity should be a numeric value", 400)

    classification = request.args.get('classification')
    if classification and len(classification) > 140:
        raise InvalidUsage("Classification string too long", 400)

    build = request.args.get('build')
    if build and len(build) > 256:
        raise InvalidUsage("Build string too long", 400)

    machine_id = request.args.get('machine_id')
    if machine_id and len(machine_id) > 32:
        raise InvalidUsage("Machine id too long", 400)

    created_in_days = None
    created_in_sec = None
    interval_sec = None

    created_in_days = request.args.get('created_in_days')
    if created_in_days:
        if not created_in_days.isdigit():
            raise InvalidUsage("created_in_days should be a numeric value", 400)

        created_in_days = int(created_in_days)

        if int(created_in_days) < 0:
            raise InvalidUsage("created_in_sec should not be negative", 400)
        elif created_in_days > 30:
            created_in_days = 30
        interval_sec = 24 * 60 * 60 * created_in_days
    else:
        created_in_sec = request.args.get('created_in_sec')

        if created_in_sec:
            if not created_in_sec.isdigit():
                raise InvalidUsage("created_in_sec should be a numeric value", 400)

            interval_sec = int(created_in_sec)
            if interval_sec < 0:
                raise InvalidUsage("created_in_sec should not be negative", 400)
            else:
                max_interval_sec = 24 * 60 * 60 * 30
                if interval_sec > max_interval_sec:
                    interval_sec = max_interval_sec

    limit = request.args.get('limit')
    if limit is None:
        limit = 10000
    elif not limit.isdigit():
        raise InvalidUsage("Limit should be a numeric value", 400)

    records = Record.query_records(build, classification, severity, machine_id, limit, interval_sec)
    record_list = [Record.to_dict(rec) for rec in records]

    return jsonify(records=record_list)


# vi: ts=4 et sw=4 sts=4

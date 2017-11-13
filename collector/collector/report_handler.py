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
from .lib.validation import (
    validate_header,
    record_format_version_headers_validation,
    InvalidUsage)
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
MAX_NUM_RECORDS = '1000'
MAX_INTERVAL_SEC = 24 * 60 * 60 * 30    # 30 days in seconds


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


def validate_header_value(header_value, record_name, err_msg):
    try:
        if validate_header(record_name, header_value) is True:
            return header_value
    except Exception as e:
        err_msg = "Error parsing {}, {}".format(record_name, e)
    raise InvalidUsage(err_msg, 400)


def collector_post_handler():

    # The collector only accepts records with the configured TID value.
    # Make sure the TID in the collector config.py matches the TID
    # configured for telemetrics-client on the systems from which this
    # collector receives records.
    tid_header = request.headers.get("X-Telemetry-TID")
    validate_header_value(tid_header, "tid_header", "Telemetry ID mismatch")

    record_format_version = request.headers.get("Record-Format-Version")
    validate_header_value(record_format_version, "record_format_version", "Record-Format-Version is invalid")

    if record_format_version_headers_validation(record_format_version, request.headers) is not True:
        raise InvalidUsage("Record-Format-Version headers are invalid", 400)

    severity = request.headers.get("Severity")
    validate_header_value(severity, "severity", "severity value is out of range")

    classification = request.headers.get("Classification")
    validate_header_value(classification, "classification", "Classification value is invalid")

    machine_id = request.headers.get("Machine-Id")
    validate_header_value(machine_id, "machine_id", "Machine id value is invalid")

    timestamp = request.headers.get("Creation-Timestamp")
    validate_header_value(timestamp, "timestamp", "timestamp is invalid")

    ts_capture = int(timestamp)
    ts_reception = time.time()

    architecture = request.headers.get("Arch")
    validate_header_value(architecture, "architecture", "architecture is invalid")

    host_type = request.headers.get("Host-Type")
    validate_header_value(host_type, "host_type", "host type is invalid")

    kernel_version = request.headers.get("Kernel-Version")
    validate_header_value(kernel_version, "kernel_version", "kernel version is invalid")

    if record_format_version == '2':
        board_name = "N/A"
        cpu_model = "N/A"
        bios_version = "N/A"

    elif record_format_version == '3':
        board_name = request.headers.get("Board-Name")
        validate_header_value(board_name, "board_name", "board name is invalid")

        cpu_model = request.headers.get("Cpu-Model")
        validate_header_value(cpu_model, "cpu_model", "cpu model is invalid")

        bios_version = request.headers.get("Bios-Version")
        validate_header_value(bios_version, "bios_version", "BIOS version is invalid")
    else:
        board_name = ""
        cpu_model = ""
        bios_version = ""

    os_name = request.headers.get('System-Name')
    os_name = os_name.replace('"', '').replace("'", "")
    build = request.headers.get('Build')
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

    payload_format_version = request.headers.get("Payload-Format-Version")
    validate_header_value(payload_format_version, "payload_format_version",
                          "Payload format version outside of range supported")

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

    db_class = Classification.query.filter_by(classification=classification).first()
    if db_class is None:
        db_class = Classification(classification)

    db_build = Build.query.filter_by(build=build).first()
    if db_build is None:
        db_build = Build(build)

    db_rec = Record.create(machine_id, host_type, severity, db_class, db_build, architecture, kernel_version,
                           record_format_version, ts_capture, ts_reception, payload_format_version, os_name,
                           board_name, bios_version, cpu_model, external, payload)

    if is_crash_classification(classification):
        # must pass args as bytes to uwsgi under Python 3
        process_guilties(klass=classification.encode(), id=str(db_rec.id).encode())

    resp = jsonify(db_rec.to_dict())
    resp.status_code = 201
    return resp


def get_records_api_handler():
    query_filter = {}

    params = ['severity', 'classification', 'build', 'machine_id', 'created_in_days', 'created_in_sec', 'limit']

    # Build filter query
    for param in params:
        param_val = request.args.get(param, None)
        if param_val is not None:
            query_filter.update({param: param_val})

    # Validate query parameters correctness
    if not query_filter.get('severity', '123').isdigit():
        raise InvalidUsage("Severity should be a numeric value", 400)

    if len(query_filter.get('classification', 'abc')) > 140:
        raise InvalidUsage("Classification string too long", 400)

    if len(query_filter.get('build', '1234')) > 256:
        raise InvalidUsage("Build string too long", 400)

    if len(query_filter.get('machine_id', '1234')) > 32:
        raise InvalidUsage("Machine id too long", 400)

    if not query_filter.get('created_in_days', '123').isdigit():
        raise InvalidUsage("created_in_days should be a numeric value", 400)

    if not query_filter.get('created_in_sec', '123').isdigit():
        raise InvalidUsage("created_in_sec should be a numeric value", 400)

    if not query_filter.get('created_in_days', 123) > 0:
        raise InvalidUsage("created_in_days should not be negative", 400)

    if not query_filter.get('created_in_sec', 123) > 0:
        raise InvalidUsage("created_in_sec should not be negative", 400)

    if not query_filter.get('limit', '1000').isdigit():
        raise InvalidUsage("Limit should not be negative", 400)

    created_in_days = query_filter.get('created_in_days', None)
    created_in_sec = query_filter.get('created_in_sec', None)
    interval_sec = None

    if created_in_days is not None:
        created_in_days = int(created_in_days)
        interval_sec = 24 * 60 * 60 * created_in_days
    elif created_in_sec is not None:
        interval_sec = int(created_in_sec)

    if interval_sec is not None and interval_sec > MAX_INTERVAL_SEC:
        interval_sec = MAX_INTERVAL_SEC

    limit = query_filter.get('limit', MAX_NUM_RECORDS)
    build = query_filter.get('build', None)
    classification = query_filter.get('classification', None)
    severity = query_filter.get('severity', None)
    machine_id = query_filter.get('machine_id', None)

    records = Record.query_records(build, classification, severity, machine_id, limit, interval_sec)
    record_list = [Record.to_dict(rec) for rec in records]

    return jsonify(records=record_list)

# ########## Routes ###########


@app.route("/", methods=['GET', 'POST'])
@app.route("/v2/collector", methods=['GET', 'POST'])
def handler():
    if request.method == 'POST':
        return collector_post_handler()
    else:
        return redirect("/telemetryui", code=302)


@app.route("/api/records", methods=['GET'])
def records_api_handler():
    """
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

    """
    return get_records_api_handler()


# vi: ts=4 et sw=4 sts=4

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
    validate_query,
    MAX_NUM_RECORDS,
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


def clean_build_n_value(build):
    # It is common to see the build numbers quoted in os-release. We don't
    # need the quotes, so strip them from the semantic value.
    _build = build.replace('"', '').replace("'", "")
    return _build


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

    record_format_version_headers_validation(record_format_version, request.headers)

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

    board_name = "N/A"
    cpu_model = "N/A"
    bios_version = "N/A"

    if record_format_version >= '3':
        board_name = request.headers.get("Board-Name")
        validate_header_value(board_name, "board_name", "board name is invalid")

        cpu_model = request.headers.get("Cpu-Model")
        validate_header_value(cpu_model, "cpu_model", "cpu model is invalid")

        bios_version = request.headers.get("Bios-Version")
        validate_header_value(bios_version, "bios_version", "BIOS version is invalid")

    os_name = request.headers.get('System-Name')
    os_name = os_name.replace('"', '').replace("'", "")
    build = request.headers.get('Build')
    build = clean_build_n_value(build)
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


def validate_query_value(query_value, query_name, err_msg):
    try:
        if validate_query(query_name, query_value) is True:
            return query_value
    except Exception as e:
        err_msg = "Error parsing {}, {}".format(query_name, e)
    raise InvalidUsage(err_msg, 400)


def get_records_api_handler():

    # Validate query parameters correctness
    severity = request.args.get("severity", None)
    if severity is not None:
        validate_query_value(severity, "severity", "Severity should be a numeric value")

    classification = request.args.get('classification', None)
    if classification is not None:
        validate_query_value(classification, "classification", "Classification value is invalid")

    build = request.args.get('build', None)
    if build is not None:
        build = clean_build_n_value(build)
        validate_query_value(build, "build", "Build value is invalid")

    machine_id = request.args.get('machine_id', None)
    if machine_id is not None:
        validate_query_value(machine_id, "machine_id", "Machine id value is invalid")

    created_in_days = request.args.get('created_in_days', None)
    if created_in_days is not None:
        validate_query_value(created_in_days, "created_in_days", "Created (in days) value is invalid")

    created_in_sec = request.args.get('created_in_sec', None)
    if created_in_sec is not None:
        validate_query_value(created_in_sec, "created_in_sec", "Created (in seconds) value is invalid")

    limit = request.args.get('limit', MAX_NUM_RECORDS)
    if limit != MAX_NUM_RECORDS:
        validate_query_value(limit, "limit", "Record limit value is invalid")

    # Transform days interval to seconds
    if created_in_days is not None:
        created_in_days = int(created_in_days)
        interval_sec = 24 * 60 * 60 * created_in_days
    elif created_in_sec is not None:
        interval_sec = int(created_in_sec)
    else:
        interval_sec = MAX_INTERVAL_SEC

    if interval_sec is not None and interval_sec > MAX_INTERVAL_SEC:
        interval_sec = MAX_INTERVAL_SEC

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

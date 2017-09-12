import re
import time
from flask import (
    request,
    jsonify)
from collector import app
from ..model import (
    Record,
    Classification,
    Build)
from ..crash import (
    process_guilties,
    is_crash_classification)

REQUIRED_HEADERS = (
    'X-Telemetry-Tid',
    'Record-Format-Version',
    'Severity',
    'Classification',
    'Machine-Id',
    'Creation-Timestamp',
    'Arch',
    'Host-Type',
    'Kernel-Version',
    'Board-Name',
    'Cpu-Model',
    'Bios-Version',
    'System-Name',
    'Build',
    'Payload-Format-Version'
)

# see config.py for the meaning of this value #
TELEMETRY_ID = app.config.get("TELEMETRY_ID", "6907c830-eed9-4ce9-81ae-76daf8d88f0f")

POSTGRES_INT_MAX = 2147483647

MAX_NUM_RECORDS = '1000'


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


def validate_headers(headers):
    req_headers = dict(headers)
    req_headers_keys = req_headers.keys()
    for header in REQUIRED_HEADERS:
        if header not in req_headers_keys:
            raise InvalidUsage("Request header {} is missing".format(header), 400)
        if not request.headers.get(header):
            raise InvalidUsage("Request header {} is blank".format(header), 400)
    return True


def collector_post_handler():
    validate_headers(request.headers)

    tid_header = request.headers.get('X-Telemetry-TID')

    # The collector only accepts records with the configured TID value.
    # Make sure the TID in the collector config.py matches the TID
    # configured for telemetrics-client on the systems from which this
    # collector receives records.
    if tid_header != TELEMETRY_ID:
        err = "Telemetry ID mismatch. Expected: {}; Actual: {}".format(TELEMETRY_ID, tid_header)
        raise InvalidUsage(err, 400)

    record_format_version = request.headers.get('Record-Format-Version')
    severity = request.headers.get('Severity')
    classification = request.headers.get('Classification')
    machine_id = request.headers.get('Machine-Id')
    if len(machine_id) > 32:
        raise InvalidUsage("Machine id too long", 400)
    timestamp = request.headers.get('Creation-Timestamp')
    ts_capture = int(timestamp)
    ts_reception = time.time()

    architecture = request.headers.get('Arch')
    host_type = request.headers.get('Host-Type')
    kernel_version = request.headers.get('Kernel-Version')
    board_name = request.headers.get('Board-Name')
    cpu_model = request.headers.get('Cpu-Model')
    bios_version = request.headers.get('Bios-Version')
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

    payload_format_version = request.headers.get('Payload-Format-Version')
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
                           board_name, bios_version, cpu_model, external, payload)

    if is_crash_classification(classification):
        # must pass args as bytes to uwsgi under Python 3
        process_guilties(klass=classification.encode(), id=str(db_rec.id).encode())

    resp = jsonify(db_rec.to_dict())
    resp.status_code = 201
    return resp


def collector_get_api_handler():
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

# vi: ts=4 et sw=4 sts=4

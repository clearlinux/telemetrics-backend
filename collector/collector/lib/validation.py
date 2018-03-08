#
# Copyright 2015-2018 Intel Corporation
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

import string
from .. import app
MAX_NUM_RECORDS = '1000'

REQUIRED_HEADERS_V1 = (
    'Arch',
    'Build',
    'Creation-Timestamp',
    'Classification',
    'Host-Type',
    'Kernel-Version',
    'Machine-Id',
    'Severity',
    'Record-Format-Version',
)

REQUIRED_HEADERS_V2 = REQUIRED_HEADERS_V1 + (
    'Payload-Format-Version',
    'System-Name',
    'X-Telemetry-Tid',
)

REQUIRED_HEADERS_V3 = REQUIRED_HEADERS_V2 + (
    'Board-Name',
    'Bios-Version',
    'Cpu-Model',
)

REQUIRED_HEADERS_V4 = REQUIRED_HEADERS_V3 + (
     'Event-Id',
)

# see config.py for the meaning of this value
TELEMETRY_ID = app.config.get("TELEMETRY_ID", "6907c830-eed9-4ce9-81ae-76daf8d88f0f")

SEVERITY_VALUES = [1, 2, 3, 4]
VALID_RECORD_FORMAT_VERSIONS = [1, 2, 3, 4]
POSTGRES_INT_MAX = 2147483647
MAXLEN_PRINTABLE = 200


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


def validate_headers(headers, required_headers):
    """ Check for every single required header to be
        in the request """
    req_headers = dict(headers)
    req_headers_keys = req_headers.keys()
    for header in required_headers:
        if header not in req_headers_keys:
            raise InvalidUsage("Record-Format-Version headers are invalid, {} missing".format(header), 400)
    return True


def is_not_none(v):
    return v is not None


def is_a_number(n):
    return str(n).isdigit()


def value_is_printable(a_value):
    return all([x in string.printable for x in a_value])


def record_format_version_validation(record_format_version):
    return all([is_not_none(record_format_version), is_a_number(record_format_version)]) and int(record_format_version) in VALID_RECORD_FORMAT_VERSIONS


def record_format_version_headers_validation(record_format_version, headers):
    # Validate required headers based on Record Version
    req_headrs = {
        '1': REQUIRED_HEADERS_V1,
        '2': REQUIRED_HEADERS_V2,
        '3': REQUIRED_HEADERS_V3,
        '4': REQUIRED_HEADERS_V4,
    }
    reqs = req_headrs.get(record_format_version, None)
    if reqs is None:
        return False
    return validate_headers(headers, reqs)


def validation_tid_header(tid):
    return tid == TELEMETRY_ID


def validate_severity(severity):
    return is_a_number(severity) and int(severity) in SEVERITY_VALUES


def validate_classification(classification):
    return is_not_none(classification) and len(classification.split('/')) == 3


def validate_machine_id(machine_id):
    return is_not_none(machine_id) and len(machine_id) <= 32


def validate_timestamp(timestamp):
    return all([is_not_none(timestamp), is_a_number(timestamp)])


def validate_architecture(arch):
    return arch in ["armv7l", "armv6l", "amd64", "sparc64", "ppc64", "i686", "i386", "x86_64", "ppc"]


def validate_host_type(host_type):
    return is_not_none(host_type) and len(host_type) < 250


def validate_kernel_version(kernel_version):
    """ makes sure that the kernel version string has at least 2 numbers
        version, major and minor revision
    """
    try:
        version, major_revision, _ = str(kernel_version).split('.', maxsplit=2)
        return all([is_a_number(x) for x in [version, major_revision]])
    except ValueError as e:
        print(e)
        return False


def validate_payload_format_version(payload_format_version):
    return int(payload_format_version) < POSTGRES_INT_MAX


def validate_x_header(header_value):
    return is_not_none(header_value) and len(header_value) < MAXLEN_PRINTABLE and value_is_printable(header_value)


def validate_created(created):
    return is_a_number(created)


def validate_record_limit(limit):
    return is_a_number(limit) and limit <= MAX_NUM_RECORDS


def validate_event_id(header_value):
    return len(header_value) == 32 and len([v for v in header_value if v in "0123456789abcdef"]) == 32


def validate_header(name, value, expected=None):
    if expected is None:
        return {
            'tid_header': validation_tid_header,
            'record_format_version': record_format_version_validation,
            'payload_format_version': validate_payload_format_version,
            'severity': validate_severity,
            'classification': validate_classification,
            'machine_id': validate_machine_id,
            'timestamp': validate_timestamp,
            'architecture': validate_architecture,
            'host_type': validate_host_type,
            'kernel_version': validate_kernel_version,
            'board_name': validate_x_header,
            'cpu_model': validate_x_header,
            'bios_version': validate_x_header,
            'build': validate_x_header,
            'event_id': validate_event_id,
        }.get(name, lambda x: False)(value)
    else:
        return value == expected


def validate_query(name, value):
    return {
        'severity': validate_severity,
        'classification': validate_classification,
        'build': validate_x_header,
        'limit': validate_record_limit,
        'machine_id': validate_machine_id,
        'created_in_days': validate_created,
        'created_in_sec': validate_created,
    }.get(name, lambda x: False)(value)

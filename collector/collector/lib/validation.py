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

import string
from .. import app

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

# see config.py for the meaning of this value
TELEMETRY_ID = app.config.get("TELEMETRY_ID", "6907c830-eed9-4ce9-81ae-76daf8d88f0f")

SEVERITY_VALUES = [1, 2, 3, 4]
VALID_RECORD_FORMAT_VERSIONS = [1, 2, 3]
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
            return False
    return True


def record_format_version_validation(record_format_version):
    return record_format_version and int(record_format_version) in VALID_RECORD_FORMAT_VERSIONS


def record_format_version_headers_validation(record_format_version, headers):
    # Validate required headers based on Record Version
    if int(record_format_version) == 1:
        return validate_headers(headers, REQUIRED_HEADERS_V1)
    elif int(record_format_version) == 2:
        return validate_headers(headers, REQUIRED_HEADERS_V2)
    elif int(record_format_version) == 3:
        return validate_headers(headers, REQUIRED_HEADERS_V3)
    return False


def value_is_printable(a_value):
    return all([x in string.printable for x in a_value])


def validation_tid_header(tid):
    return tid == TELEMETRY_ID


def validate_severity(severity):
    return severity not in SEVERITY_VALUES


def validate_classification(classification):
    return classification is not None and len(classification.split('/')) == 3


def validate_machine_id(machine_id):
    return machine_id is not None and len(machine_id) <= 32


def validate_timestamp(timestamp):
    """ Verify that the ts is at least > 01/01/2017"""
    return timestamp is not None and \
           str(timestamp).isdigit() and \
           int(timestamp) > 1483232400 & len(str(timestamp)) == 10 & str(timestamp).isdigit()


def validate_architecture(arch):
    return arch in ["armv7l", "armv6l", "amd64", "sparc64", "ppc64", "i686", "i386", "x86_64", "ppc"]


def validate_host_type(host_type):
    return host_type and len(host_type) < 250


def validate_kernel_version(kernel_version):
    """ makes sure that the kernel version string has at least 3 numbers
        version, major and minor revision
    """
    try:
        version, major_revision, _ = str(kernel_version).split('.', maxsplit=2)
        minor_version, _ = str(_).split('-', maxsplit=1)
        return all([x.isdigit() for x in [version, major_revision, minor_version]])
    except ValueError as e:
        print(e)
        return False


def validate_payload_format_version(payload_format_version):
    return int(payload_format_version) < POSTGRES_INT_MAX


def validate_x_header(header_value):
    return header_value is not None and len(header_value) < MAXLEN_PRINTABLE and value_is_printable(header_value)


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
        }.get(name, lambda x: False)(value)
    else:
        return value == expected

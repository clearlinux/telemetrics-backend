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

import unittest
from collector import (
    app,
    db,
    report_handler,)
from flask import current_app

classification = 'classification'
severity = 'severity'
kernel_version = 'kernel_version'
record_version = 'record_format_version'
machine_id = 'machine_id'
host_type = 'host_type'
arch = 'arch'
build = 'build'
timestamp = 'creation_timestamp'
tid = 'X-Telemetry-Tid'
board_name = 'Board-Name'
cpu_model = 'Cpu-Model'
bios_version = 'Bios-Version'
system_name = 'System-Name'
payload_version = 'Payload-Format-Version'
event_id = 'Event-Id'


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


def get_record_v1():
    return {
        arch: 'x86_64',
        build: '550',
        timestamp: 1483232401,
        classification: 'a/b/c',
        host_type: 'LenovoT20',
        kernel_version: '3.16.4-123.generic',
        machine_id: '1234',
        severity: 2,
        record_version: 1,
    }


def get_record_v2():
    v2 = get_record_v1()
    v2.update({
        record_version: 2,
        tid: '6907c830-eed9-4ce9-81ae-76daf8d88f0f',
        system_name: 'clear-linux-os',
        payload_version: 1
    })
    return v2


def get_record_v3():
    v3 = get_record_v2()
    v3.update({
        record_version: 3,
        board_name: 'D54250WYK|Intel Corporation',
        cpu_model: 'Intel(R) Core(TM) i5-4250U CPU @ 1.30GHz',
        bios_version: 'WYLPT10H.86A.0041.2015.0720.1108',

    })
    return v3


def get_record_v4():
    v4 = get_record_v3()
    v4.update({
        record_version: 4,
        event_id: '39cc109a1079df96376693ebc7a0f632',
    })
    return v4


def get_record():
    return {
        "X-Telemetry-TID": "6907c830-eed9-4ce9-81ae-76daf8d88f0f",
        "record_format_version": "2",
        "severity": "1",
        "classification": "org.clearlinux/hello/world",
        "machine_id": "clr-linux-avj01",
        "creation_timestamp": "1505235249",
        "arch": "x86_64",
        "host_type": "blank|blank|blank",
        "kernel_version": "4.12.5-374.native",
        "system_name": "clear-linux-os",
        "build": "17700",
        "payload_format_version": "1",
        "board_name": "D54250WYK|Intel Corporation",
        "cpu_model": "Intel(R) Core(TM) i5-4250U CPU @ 1.30GHz",
        "bios_version": "WYLPT10H.86A.0041.2015.0720.1108"
    }


class RecordTestCases(unittest.TestCase):
    """ Generic object for telemetry record tests """

    def setUp(self):
        app.testing = True
        app.config.from_object('collector.config_local.Testing')
        app.debug = False
        self.app_context = app.app_context()
        self.app_context.push()
        db.init_app(current_app)
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def missing_header(self, header, header_name):
        headers = self.get_version_records()
        del headers[header_name]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)

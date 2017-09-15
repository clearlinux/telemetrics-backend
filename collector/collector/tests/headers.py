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
from collector import app, db
from flask import current_app
import json

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
        timestamp: 2752515,
        classification: 'test/invalid',
        host_type: 'LenovoT20',
        kernel_version: '3.16',
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


class RecordTestCases(unittest.TestCase):
    """ Generic object for telemetry record tests """

    def setUp(self):
        app.testing = True
        app.config.from_object('config_local.Testing')
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
        self.assertTrue(header in response.data.decode('utf-8'))


class TestHandlerRecordV2(RecordTestCases):
    """
        Tests record creation for record version 2 and headers validation
    """
    @staticmethod
    def get_version_records():
        return get_record_v2()

    def test_record_created(self):
        headers = get_record_v2()
        data = "hello"
        response = self.client.post('/', headers=headers, data=data)
        self.assertTrue(response.status_code == 201)
        json_resp = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_resp['classification'] == headers[classification])
        self.assertTrue(json_resp['severity'] == headers[severity])
        self.assertTrue(json_resp['kernel_version'] == headers[kernel_version])
        self.assertTrue(json_resp['record_format_version'] == headers[record_version])
        self.assertTrue(json_resp['machine_id'] == headers[machine_id])
        self.assertTrue(json_resp['machine_type'] == headers[host_type])
        self.assertTrue(json_resp['arch'] == headers[arch])
        self.assertTrue(json_resp['build'] == headers[build])
        self.assertTrue(json_resp['payload'] == data)

    def test_post_fail_missing_classifiction(self):
        headers = get_record_v2()
        del headers[classification]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Classification' in response.data.decode('utf-8'))

    def missing_header(self, header, header_name):
        headers = get_record_v2()
        del headers[header_name]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue(header in response.data.decode('utf-8'))

    def test_post_fail_missing_severity(self):
        self.missing_header('Severity', severity)

    def test_post_fail_missing_kernel_version(self):
        self.missing_header('Kernel-Version', kernel_version)

    def test_post_fail_missing_host_type(self):
        self.missing_header('Host-Type', host_type)

    def test_post_fail_missing_machine_id(self):
        self.missing_header('Machine-Id', machine_id)

    def test_post_fail_missing_arch(self):
        self.missing_header('Arch', arch)

    def test_post_fail_missing_build(self):
        self.missing_header('Build', build)

    def test_post_fail_missing_record_version(self):
        self.missing_header('Record-Format-Version', record_version)


class TestHandlerRecordTransitionV2toV3(RecordTestCases):
    """
        This test case tests a transition where the client is in record
        version 2 though is sending v3 headers, make sure the server
        understands the record as v2 and do not have problems creating it
    """
    def test_record_created(self):
        headers = get_record_v3()
        data = "hello"
        response = self.client.post('/', headers=headers, data=data)
        self.assertTrue(response.status_code == 201)
        json_resp = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_resp['classification'] == headers[classification])
        self.assertTrue(json_resp['severity'] == headers[severity])
        self.assertTrue(json_resp['kernel_version'] == headers[kernel_version])
        self.assertTrue(json_resp['record_format_version'] == headers[record_version])
        self.assertTrue(json_resp['machine_id'] == headers[machine_id])
        self.assertTrue(json_resp['machine_type'] == headers[host_type])
        self.assertTrue(json_resp['arch'] == headers[arch])
        self.assertTrue(json_resp['build'] == headers[build])


class TestHandlerRecordV3(RecordTestCases):
    """
        Test record v3 making sure to validate expected headers for v3
        if record version is properly set to 3.
    """
    @staticmethod
    def get_version_records():
        return get_record_v3()

    def test_post_record_v3_with_headers_v2(self):
        headers = get_record_v2()
        headers.update({record_version: 3, })
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue(board_name in response.data.decode('utf-8'))

    def test_post_record_v3(self):
        headers = get_record_v3()
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 201)

    def test_post_missing_cpu_model(self):
        self.missing_header('Cpu-Model', cpu_model)

    def test_post_missing_board_name(self):
        self.missing_header('Board-Name', board_name)

    def test_post_missing_bios_version(self):
        self.missing_header('Bios-Version', bios_version)


if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    unittest.main()


# vi: ts=4 et sw=4 sts=4

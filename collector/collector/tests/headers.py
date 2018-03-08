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
import json
from collector.tests.testcase import (
    RecordTestCases,
    classification,
    severity,
    kernel_version,
    record_version,
    machine_id,
    host_type,
    arch,
    build,
    timestamp,
    tid,
    board_name,
    cpu_model,
    bios_version,
    system_name,
    payload_version,
    event_id,
    get_record_v1,
    get_record_v2,
    get_record_v3,
    get_record_v4,)


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
        self.assertTrue(response.status_code == 201, response.data.decode('utf-8'))
        json_resp = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_resp['classification'] == headers[classification])
        self.assertTrue(str(json_resp['severity']) == str(headers[severity]))
        self.assertTrue(json_resp['kernel_version'] == headers[kernel_version])
        self.assertTrue(str(json_resp['record_format_version']) == str(headers[record_version]))
        self.assertTrue(json_resp['machine_id'] == headers[machine_id])
        self.assertTrue(json_resp['machine_type'] == headers[host_type])
        self.assertTrue(json_resp['arch'] == headers[arch])
        self.assertTrue(json_resp['build'] == headers[build])
        self.assertTrue(json_resp['payload'] == data)

    def missing_header(self, header, header_name):
        headers = get_record_v2()
        del headers[header_name]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400, response.data.decode('utf-8'))

    def test_post_fail_missing_classifiction(self):
        self.missing_header('Classification', severity)

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
        self.assertTrue(response.status_code == 201, response.data.decode('utf-8'))
        json_resp = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_resp['classification'] == headers[classification])
        self.assertTrue(int(json_resp['severity']) == int(headers[severity]))
        self.assertTrue(json_resp['kernel_version'] == headers[kernel_version])
        self.assertTrue(int(json_resp['record_format_version']) == int(headers[record_version]))
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
        self.assertTrue(response.status_code == 400, response.data.decode('utf-8'))

    def test_post_record_v3(self):
        headers = get_record_v3()
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 201, response.data.decode('utf-8'))

    def test_post_missing_cpu_model(self):
        self.missing_header('Cpu-Model', cpu_model)

    def test_post_missing_board_name(self):
        self.missing_header('Board-Name', board_name)

    def test_post_missing_bios_version(self):
        self.missing_header('Bios-Version', bios_version)


class TestHandlerRecordV4(RecordTestCases):
    """
       Test record v4
    """
    @staticmethod
    def get_version_records():
        return get_record_v4()

    def test_post_record_v4(self):
       headers = get_record_v4()
       response = self.client.post('/', headers=headers, data='test')
       self.assertTrue(response.status_code == 201, response.data.decode('utf-8'))

    def test_post_missing_eid(self):
       self.missing_header('Event-Id', event_id)


if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    unittest.main()


# vi: ts=4 et sw=4 sts=4

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
from . import app, db
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


class TestHandler(unittest.TestCase):
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

    def get_api_headers(self):
        headers = {
            record_version: 1,
            classification: 'test/invalid',
            severity: 2,
            machine_id: '1234',
            timestamp: 2752515,
            arch: 'x86_64',
            host_type: 'LenovoT20',
            kernel_version: '3.16',
            build: '550'
        }
        return headers

    def test_record_created(self):
        headers = self.get_api_headers()
        data = "hello"
        response = self.client.post('/', headers=headers, data=data)
        self.assertTrue(response.status_code == 201)
        json_resp = json.loads(response.data)
        self.assertTrue(json_resp['classification'] == headers[classification])
        self.assertTrue(json_resp['severity'] == headers[severity])
        self.assertTrue(json_resp['kernel_version'] == headers[kernel_version])
        self.assertTrue(json_resp['record_format_version'] == headers[record_version])
        self.assertTrue(json_resp['machine_id'] == headers[machine_id])
        self.assertTrue(json_resp['machine_type'] == headers[host_type])
        self.assertTrue(json_resp['arch'] == headers[arch])
        self.assertTrue(json_resp['build'] == headers[build])
        self.assertTrue(json_resp['payload'] == data)
        self.assertTrue(json_resp['ts_capture'] == headers[timestamp])

    def test_post_fail_missing_classifiction(self):
        headers = self.get_api_headers()
        del headers[classification]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        json_resp = json.loads(response.data)
        self.assertTrue('Classification missing' in response.data)

    def test_post_fail_missing_severity(self):
        headers = self.get_api_headers()
        del headers[severity]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Severity missing' in response.data)

    def test_post_fail_missing_kernel_version(self):
        headers = self.get_api_headers()
        del headers[kernel_version]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Kernel version missing' in response.data)

    def test_post_fail_missing_host_type(self):
        headers = self.get_api_headers()
        del headers[host_type]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Host type missing' in response.data)

    def test_post_fail_missing_machine_id(self):
        headers = self.get_api_headers()
        del headers[machine_id]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Machine id missing' in response.data)

    def test_post_fail_missing_arch(self):
        headers = self.get_api_headers()
        del headers[arch]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Architecture missing' in response.data)

    def test_post_fail_missing_build(self):
        headers = self.get_api_headers()
        del headers[build]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Build missing' in response.data)

    def test_post_fail_missing_record_version(self):
        headers = self.get_api_headers()
        del headers[record_version]
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 400)
        self.assertTrue('Record format version missing' in response.data)

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    unittest.main()


# vi: ts=4 et sw=4 sts=4

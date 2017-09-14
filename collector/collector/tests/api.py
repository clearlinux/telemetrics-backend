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

    def test_query_report(self):
        rec = get_record()
        response = self.client.post('/', headers=rec, data='test')
        self.assertTrue(response.status_code == 201)
        filters = {
            'severity': 1,
        }
        response = self.client.get('/api/records', query_string=filters)
        resp_obj = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(resp_obj['records']), 1)
        filters1 = {
            'build': '17780',
        }
        response = self.client.get('/api/records', query_string=filters1)
        resp_obj = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(resp_obj['records']), 0)


if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    unittest.main()


# vi: ts=4 et sw=4 sts=4

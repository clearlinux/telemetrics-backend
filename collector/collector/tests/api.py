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

import json
import unittest
from collector.tests.testcase import (
    RecordTestCases,
    get_record)


class TestHandler(RecordTestCases):

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


if __name__ == '__main__':
    unittest.main()


# vi: ts=4 et sw=4 sts=4

#
# Copyright 2018 Intel Corporation
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
from collector import app
from collector.parsers.demo import main
from collector.report_handler import load_parsers
from collector.tests.testcase import (
    RecordTestCases,
    get_record_v3,)


class TestCasesParserPlugin(RecordTestCases):
    """
        Load parsers programmatically for test
    """
    def setUp(self):
        RecordTestCases.setUp(self)
        app.config['POST_PROCESSING_PARSERS'] = ["demo"]
        load_parsers()


class TestParserPlugin(TestCasesParserPlugin):
    """
        Simple test to make sure that plugins parsers are working
    """
    def test_record_created(self):
        headers = get_record_v3()
        data = "hello"
        headers['classification'] = main.CLASSIFICATIONS
        response = self.client.post('/', headers=headers, data=data)
        self.assertTrue(response.status_code == 201, response.data.decode('utf-8'))


if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    unittest.main()

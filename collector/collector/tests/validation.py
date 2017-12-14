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
from collector.tests.testcase import (
    RecordTestCases,
    get_record_v3,
    kernel_version)


class TestHandlerRecordValidation(RecordTestCases):
    """
        Test record validation
    """
    @staticmethod
    def get_version_records():
        return get_record_v3()

    def test_post_kernel_version_validation_1(self):
        headers = get_record_v3()
        headers.update({kernel_version: '3.16.generic'})
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 201, response.data.decode('utf-8'))


if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    unittest.main()


# vi: ts=4 et sw=4 sts=4

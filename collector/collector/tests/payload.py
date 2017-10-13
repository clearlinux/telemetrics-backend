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

import io
import unittest
from collector.tests.testcase_base import (
    bin_data,
    RecordTestCases,
    payload_version,
    get_record_v3)


class TestBinPayload(RecordTestCases):
    def test_binary_mutipart_form(self):
        headers = get_record_v3()
        headers[payload_version] = 200
        response = self.client.post('/', headers=headers,
                                    content_type='multipart/form-data',
                                    data={
                                        'payload': (io.BytesIO(bin_data), "binary.file")
                                    })
        self.assertTrue(response.status_code == 201)

    def test_binary_mutipart_form_no_content_type(self):
        headers = get_record_v3()
        headers[payload_version] = 200
        response = self.client.post('/', headers=headers,
                                    data={
                                        'payload': (io.BytesIO(bin_data), "binary.file")
                                    })
        self.assertTrue(response.status_code == 201)


if __name__ == '__main__' and __package__ is None:
    unittest.main()


# vi: ts=4 et sw=4 sts=4
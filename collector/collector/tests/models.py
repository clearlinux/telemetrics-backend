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

import os
import unittest
from collector.tests.testcase_base import RecordTestCases
from collector.model import Attachment


class TestAppModel(RecordTestCases):

    def assert_len(self, length, msg=''):
        self.assertEqual(len(Attachment.query.all()), length, msg)

    def test_save_and_delete(self):
        Attachment(**{
            'record_id': None,
            'file_path': os.path.join(self.test_tmp_folder.name, 'testfile'),
            'mime_type': 'application/tar+gzip',
        }).save()
        attachment = Attachment(**{
            'record_id': None,
            'file_path': os.path.join(self.test_tmp_folder.name, 'testfile1'),
            'mime_type': 'application/tar+gzip',
        })
        attachment.save()
        # double checking not part of test per se
        assert len(Attachment.query.all()) == 2
        attachment.delete()
        self.assert_len(1)

    def test_delete_with_kwargs(self):
        Attachment(**{
            'record_id': None,
            'file_path': os.path.join(self.test_tmp_folder.name, 'testfile'),
            'mime_type': 'application/tar+gzip',
        }).save()
        attachment = Attachment(**{
            'record_id': None,
            'file_path': os.path.join(self.test_tmp_folder.name, 'testfile1'),
            'mime_type': 'application/tar+gzip',
        })
        attachment.save()
        # double checking not part of test per se
        assert len(Attachment.query.all()) == 2
        attachment.delete(**{
            'id': 2000,
        })
        self.assert_len(2, "Should still be 2 since id:2000 is non existent")
        attachment.delete(**{
            'id': attachment.id,
        })
        self.assert_len(1)


if __name__ == '__main__':
    unittest.main()


# vi: ts=4 et sw=4 sts=4

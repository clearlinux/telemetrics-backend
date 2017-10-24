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
import os
import unittest
from collector import db
from collector.model import (
    Record,
    Attachment,
    PurgeMixin)
from collector.tests.testcase_base import (
    bin_data,
    payload_version,
    RecordTestCases,
    get_record_v3,)


class TestAttachmentPurge(RecordTestCases):

    def test_simple_attachment_removal(self):
        # create 2 records
        headers = get_record_v3()
        response = self.client.post('/', headers=headers, data='test')
        self.assertTrue(response.status_code == 201)
        headers[payload_version] = 200
        response = self.client.post('/', headers=headers,
                                    content_type='multipart/form-data',
                                    data={
                                        'payload': (io.BytesIO(bin_data), "binary.file")
                                    })
        self.assertTrue(response.status_code == 201)
        records = Record.query.order_by(Record.id).all()
        self.assertEqual(len(records), 2, "Must have 2 created records")
        # remove record with attachment
        db.session.delete(records[1])
        db.session.commit()
        attachments = Attachment.query.all()
        file_path = attachments[0].file_path
        self.assertTrue(os.path.exists(file_path))
        # todo: this should be testing high level operation from record removal
        # test the mixing attachment removal
        PurgeMixin.purge_attachments()
        attachments = Attachment.query.filter_by(record_id=None).all()
        self.assertEqual(len(attachments), 0, "Must have 1 marked NULL")
        self.assertFalse(os.path.exists(file_path))


if __name__ == '__main__':
    unittest.main()


# vi: ts=4 et sw=4 sts=4

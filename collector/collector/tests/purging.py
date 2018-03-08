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
import time
from collector import db
from flask import current_app
from collector.model import (
    app,
    Record,
    Classification,
    Build)

from collector.tests.testcase import (
    RecordTestCases,
    get_record,)


def get_insert_params(days_old, severity, classification):
    record = get_record()
    record["classification"] = classification
    record["severity"] = severity
    db_class = Classification.query.filter_by(classification=record["classification"]).first()
    if db_class is None:
        db_class = Classification(record["classification"])
    db_build = Build.query.filter_by(build=record["build"]).first()
    if db_build is None:
        db_build = Build(record["build"])
    return [
        record["machine_id"],
        record["host_type"],
        record["severity"],
        db_class,
        db_build,
        record["arch"],
        record["kernel_version"],
        record["record_format_version"],
        int(time.time()-3600*24*days_old),
        int(time.time()-3600*24*days_old),
        record["payload_format_version"],
        record["system_name"],
        record["board_name"],
        record["bios_version"],
        record["cpu_model"],
        "39cc109a1079df96376693ebc7a0f632",
        False,
        "Test"
    ]


class TestPurging(RecordTestCases):
    """ Generic object for telemetry record tests """

    def setUp(self):
        app.testing = True
        app.config.from_object('config_local.Testing')
        app.config["MAX_DAYS_KEEP_UNFILTERED_RECORDS"] = 5
        app.config["PURGE_FILTERED_RECORDS"] = {
            "severity": {
                1: 1,
                4: 0
            },
            "classification": {
                "test/keep/one": 0,
                "test/discard/*": 1,
            }
        }
        app.debug = False
        self.app_context = app.app_context()
        self.app_context.push()
        db.init_app(current_app)
        db.create_all()
        self.client = app.test_client()

    def test_purge_delete(self):
        Record.create(*get_insert_params(2, 1, "test/discard/one"))
        Record.create(*get_insert_params(2, 2, "test/discard/two"))
        Record.create(*get_insert_params(2, 2, "test/discard/three"))
        Record.create(*get_insert_params(2, 4, "test/discard/two"))
        Record.create(*get_insert_params(2, 4, "test/discard/three"))
        Record.create(*get_insert_params(6, 2, "test/test/one"))
        Record.create(*get_insert_params(2, 1, "test/keep/one"))
        self.assertTrue(Record.query.count() == 7)
        Record.delete_records()
        self.assertTrue(Record.query.count() == 0)

    def test_purge_keep(self):
        Record.create(*get_insert_params(6, 2, "test/keep/one"))
        Record.create(*get_insert_params(3, 2, "test/test/one"))
        Record.create(*get_insert_params(6, 4, "test/test/one"))
        Record.create(*get_insert_params(2, 4, "test/discard/three"))
        Record.create(*get_insert_params(6, 2, "test/test/one"))
        Record.create(*get_insert_params(2, 1, "test/keep/one"))
        self.assertTrue(Record.query.count() == 6)
        Record.delete_records()
        self.assertTrue(len(Record.query.all()) == 3)


if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    unittest.main()

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

import logging


class Config(object):
    DEBUG = False
    TESTING = False
    LOG_LEVEL = logging.ERROR
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres:@@db_password@@@localhost/telemdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_FILE = 'handler.log'

    # When PURGE_OLD_RECORDS == True then a purging system of old records will
    # be triggered daily. If this variable is not present, then no purging will be done.
    # If the purging system is enabled, then the following two variables must be set
    PURGE_OLD_RECORDS = True
    # The maximum retention time in days for records stored in the database
    # which do not match the filters in PURGE_FILTERED_RECORDS.
    # Use 0 to avoid deletion of all unfiltered records.
    MAX_DAYS_KEEP_UNFILTERED_RECORDS = 35
    # A dictionary in the following format:
    # {
    #     "<field_name>": {
    #         "<field_value>": <max_days_to_keep>,
    #         ...
    #         },
    #     ...
    # }
    # Currently supported fields to filter:
    # [
    #     'severity',
    #     'classification',
    #     'machine_id'
    # ]
    # Use 0 to avoid deletion of records that matches the filter.
    # If you do not want to filter records to delete, just set an empty dict '{}'
    PURGE_FILTERED_RECORDS = {
        "severity": {
            1: 5,
            4: 0
        },
        "classification": {
            "org.clearlinux/mce/*": 0,
            "org.clearlinux/hello/world": 1,
            "org.clearlinux/heartbeat/ping": 1,
        }
    }

    # The Telemetry ID (TID) accepted by this `collector` app. The ID should be a
    # random UUID, generated with (for example) `uuidgen`. The default value
    # set here is used for records from the Clear Linux OS for Intel
    # Architecture.
    TELEMETRY_ID = "6907c830-eed9-4ce9-81ae-76daf8d88f0f"


class Testing(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres:@@db_password@@@localhost/testdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = True


# vi: ts=4 et sw=4 sts=4

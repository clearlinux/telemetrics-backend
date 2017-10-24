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
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:@@db_password@@@localhost/telemdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_FILE = 'handler.log'

    # The maximum retention time for records stored in the database, measured
    # from the time received by the `collector` app.
    MAX_WEEK_KEEP_RECORDS = 5

    # The Telemetry ID (TID) accepted by this `collector` app. The ID should be a
    # random UUID, generated with (for example) `uuidgen`. The default value
    # set here is used for records from the Clear Linux OS for Intel
    # Architecture.
    TELEMETRY_ID = "6907c830-eed9-4ce9-81ae-76daf8d88f0f"

    # Upload files path
    ATTACHMENT_QUARANTINE_FOLDER = '/tmp/clrtelemetry.attachments/'


class Testing(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:@@db_password@@@localhost/testdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = True


# vi: ts=4 et sw=4 sts=4

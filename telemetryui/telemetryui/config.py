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
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres:@@db_password@@@localhost/telemetry'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_FILE = 'handler.log'
    WTF_CSRF_ENABLED = True
    SECRET_KEY = '@@flask_key@@'
    RECORDS_PER_PAGE = 50
    MAX_RECORDS_PER_PAGE = 1000


class Testing(Config):
    TESTING = True


# vi: ts=4 et sw=4 sts=4

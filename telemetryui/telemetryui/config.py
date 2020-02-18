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
import logging
import secrets

class Config(object):
    db_host = os.environ['POSTGRES_HOSTNAME']
    db_user = os.environ['POSTGRES_USER']
    db_passwd = os.environ['POSTGRES_PASSWORD']
    redis_passwd = os.environ['REDIS_PASSWD']
    redis_hostname = os.environ['REDIS_HOSTNAME']
    DEBUG = False
    TESTING = False
    LOG_LEVEL = logging.ERROR
    SQLALCHEMY_DATABASE_URI = 'postgres://{user}:{passwd}@{host}/telemetry'.format(user=db_user, passwd=db_passwd, host=db_host)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_FILE = 'handler.log'
    WTF_CSRF_ENABLED = True
    SECRET_KEY = secrets.token_hex(32)
    RECORDS_PER_PAGE = 50
    MAX_RECORDS_PER_PAGE = 1000
    REDIS_HOSTNAME = redis_hostname
    REDIS_PORT = 6379
    REDIS_PASSWD = redis_passwd

# vi: ts=4 et sw=4 sts=4

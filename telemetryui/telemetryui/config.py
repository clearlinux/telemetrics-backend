# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

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

# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import logging

class Config(object):
    db_host = os.environ.get('POSTGRES_HOSTNAME', 'db')
    db_user = os.environ.get('POSTGRES_USER', 'telemetry')
    db_passwd = os.environ.get('POSTGRES_PASSWORD','postgres')
    redis_passwd = os.environ.get('REDIS_PASSWD', '')
    redis_hostname = os.environ.get('REDIS_HOSTNAME', 'redis')
    DEBUG = False
    TESTING = False
    LOG_LEVEL = logging.ERROR
    SQLALCHEMY_DATABASE_URI = 'postgres://{user}:{passwd}@{host}/telemetry'.format(user=db_user, passwd=db_passwd, host=db_host)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_FILE = 'handler.log'
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.urandom(32)
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '')
    RECORDS_PER_PAGE = 50
    REDIS_HOSTNAME = redis_hostname
    REDIS_PORT = 6379
    REDIS_PASSWD = redis_passwd

# vi: ts=4 et sw=4 sts=4

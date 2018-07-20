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

# This configuration file can be used for a local development debug server
# at localhost:5000. Overrides the config module.

import logging


class Config(object):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = logging.ERROR

    # If your telemetry database password is not 'postgres', update this line.
    SQLALCHEMY_DATABASE_URI = 'postgres://postgres:postgres@localhost/telemetry'

    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOG_FILE = 'handler.log'
    WTF_CSRF_ENABLED = True

    # Generate a random key by running `head -c 32 /dev/urandom | base64 -`.
    # The value below is an example key generated with that command.
    SECRET_KEY = '6WbDLE0W4wON/CR7rm6P7SuI85yLCvOK02U7UeHoySQ='

    # Uncomment next line to display demo plugin, the code for the view
    # can be found under 'telemetryui/plugins/demo'
    # PLUGINS = ['demo']


class Testing(Config):
    TESTING = True


# vi: ts=4 et sw=4 sts=4

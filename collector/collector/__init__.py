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

from flask import Flask
from . import config
from flask_sqlalchemy import SQLAlchemy
from logging.handlers import RotatingFileHandler


def configure_app(config_object, app):
    app.config.from_object(config_object)
    db = SQLAlchemy(app)

app = Flask(__name__)
db = SQLAlchemy()
app.config.from_object(config.Config)

from .model import *
from . import report_handler

handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=10000, backupCount=1)
handler.setLevel(app.config['LOG_LEVEL'])
app.logger.addHandler(handler)


# vi: ts=4 et sw=4 sts=4

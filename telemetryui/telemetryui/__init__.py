# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from flask import (
    Flask)
from . import config
from .jinja_filters import (
    timesince,
    local_datetime_since,
    basename,
    get_severity_label
    )

# App instance
app = Flask(__name__, static_folder="static", static_url_path="/telemetryui/static")
app.config.from_object(config.Config)
# Load views
from .views import views_bp
# Add filters
app.add_template_filter(timesince)
app.add_template_filter(local_datetime_since)
app.add_template_filter(basename)
app.add_template_filter(get_severity_label)
# Register routes
app.register_blueprint(views_bp, url_prefix="/{}".format(app.config.get('APPLICATION_ROOT', '')))

# vi: ts=4 et sw=4 sts=4

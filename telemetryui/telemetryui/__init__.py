# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from flask import (
    Flask,
    request,
    url_for)
from . import config
from .jinja_filters import (
    timesince,
    local_datetime_since,
    basename,
    get_severity_label
    )
import importlib

app = Flask(__name__, static_folder="static", static_url_path="/telemetryui/static")
app.config.from_object(config.Config)

from . import views


def url_for_other_page(page, page_size=None):
    args = request.args.copy()
    if page_size is not None:
        args['page_size'] = page_size
    return url_for(request.endpoint, page=page, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.add_template_filter(timesince)
app.add_template_filter(local_datetime_since)
app.add_template_filter(basename)
app.add_template_filter(get_severity_label)


# vi: ts=4 et sw=4 sts=4

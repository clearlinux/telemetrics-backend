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

import re
import datetime
from flask import (
    request,
    jsonify,
    redirect)
from .purge import *
from .lib.report_handler import (
    collector_post_handler,
    collector_get_api_handler,
    InvalidUsage)


MAX_INTERVAL_SEC = 24 * 60 * 60 * 30
MAX_NUM_RECORDS = '1000'


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.before_request
def before_request():
    app.logger.info('\t'.join([
        datetime.datetime.today().ctime(),
        request.method,
        request.url,
        str(request.data),
        ', '.join([': '.join(x) for x in request.headers])])
    )


@app.route("/", methods=['GET', 'POST'])
@app.route("/v2/collector", methods=['GET', 'POST'])
def handler():
    if request.method == 'POST':
        return collector_post_handler()
    else:
        return redirect("/telemetryui", code=302)


@app.route("/api/records", methods=['GET'])
def records_api_handler():
    """
    query filters for simple query:
    classification
    severity
    build
    machine_id
    created_in_days - records created after given days
    created_in_sec - records created after given seconds

    TODO: Advanced query with pagination and following parameters?
    client_created_after - timestamp
    client_created_before - timestamp
    server_created_after - timestamp
    server_created_before - timestamp

    """

    return collector_get_api_handler()


# vi: ts=4 et sw=4 sts=4

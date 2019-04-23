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

from .model import Record
from . import app

try:
    import uwsgi
    from uwsgidecorators import cron

    PURGE_OLD_RECORDS = app.config.get("PURGE_OLD_RECORDS", True)

    # Runs cron job at 4:30 every day
    @cron(30, 4, -1, -1, -1, target='spooler')
    def purge_task(signum):
        if PURGE_OLD_RECORDS:
            app.logger.info("Running cron job for purging records")
            with app.app_context():
                Record.delete_records()

except ImportError:
        app.logger.info("Import error for uwsgi")


# vi: ts=4 et sw=4 sts=4

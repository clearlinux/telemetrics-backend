# Copyright (C) 2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import luigi
import psycopg2
from processing.main import (
    connect,
    init_guilty_blacklist,
    get_latest_id,
    get_crashes,
    process_crashes,
)

from processing import crash


class GlobalParams(luigi.Config):

    db_name = os.environ['POSTGRES_DB']
    db_host = os.environ['POSTGRES_HOSTNAME']
    db_user = os.environ['POSTGRES_USER']
    db_passwd = os.environ['POSTGRES_PASSWORD']


class ProcessCrashes(luigi.Task):
    """
        process.py ProcessCrashes --local-scheduler
    """
    is_complete = False

    def complete(self):
        return self.is_complete

    def run(self):
        db = connect(GlobalParams())
        cur = db.cursor()
        crash.GUILTY_BLACKLIST = init_guilty_blacklist(cur)
        last_id = get_latest_id(cur)
        print("#### Start processing after record id: {}".format(last_id))
        crashes = get_crashes(cur, last_id)
        print("#### Will process [{}] crashes".format(len(crashes)))
        process_crashes(cur, crashes)
        print("#### Done processing\n")
        cur.close()
        db.close()
        self.is_complete = True


if __name__ == "__main__":
    luigi.run()

# vi: ts=4 et sw=4 sts=4

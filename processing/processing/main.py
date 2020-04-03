# Copyright (C) 2015-2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import psycopg2
from . import crash
from .crash import (
     parse_crash,
     BACKTRACE_CLASSES as classifications,
)


PROCESSED_VIEW = """last_processed"""

CRASHES = """
  SELECT id, payload, classification FROM records WHERE classification in {} AND id > {} ORDER BY id ASC
"""

INSERT_GUILTY = """
  INSERT INTO {}.guilty (function, module, hide) VALUES (%s, %s, False) ON CONFLICT (function, module) DO NOTHING RETURNING id
"""

GUILTY_BLACKLIST = """
  SELECT function, module FROM guilty_blacklisted
"""

LAST_ID = """
  SELECT last_id  FROM {} LIMIT 1
""".format(PROCESSED_VIEW)

UPDATE_PROCESSED_RECORD = """
   UPDATE records SET processed = True WHERE id = %s
"""

CHECK_GUILTY = """
  SELECT id FROM {}.guilty WHERE function = %s AND module = %s
"""

UPDATE_GUILTY = """
   UPDATE records SET guilty_id = %s WHERE id = %s
"""


class GuilyBlacklist(object):

    def __init__(self, blacklisted):
        self.blacklisted = blacklisted

    def contains(self, item):
        return item in self.blacklisted


def init_guilty_blacklist(cur):
    cur.execute(GUILTY_BLACKLIST)
    rows = cur.fetchall()
    bl = [(row[0], row[1]) for row in rows]
    return GuilyBlacklist(bl)


def get_latest_id(cur):
    cur.execute(LAST_ID)
    row = cur.fetchone()
    if row[0] is None:
       return 0
    return row[0]


def get_crashes(cur, last_id):
    classifications_str = "('{}')".format("', '".join(classifications))
    cur.execute(CRASHES.format(classifications_str, last_id))
    rows = cur.fetchall()
    return rows


def process_crashes(cur, crashes, schema="public", debug=False):
    if len(crashes) == 0:
        return
    insert_guilty = INSERT_GUILTY.format(schema)
    for rid, backtrace, _ in crashes:
        if backtrace is None:
            print("## backtrace record {} is None".format(rid))
            continue
        function, module = parse_crash(backtrace)
        if function is not None and module is not None:
            # Save new function and module
            cur.execute(insert_guilty, (function, module,))
            # Row will have a value only when insertion happens
            row = cur.fetchone()
            if row is None:
                check_guilty = CHECK_GUILTY.format(schema)
                cur.execute(check_guilty, (function, module,))
                row = cur.fetchone()
            gid = row[0]
            ### Update record table with guilty_id
            cur.execute(UPDATE_GUILTY, (gid, rid,))
        else:
            print("## function or module is None for record id {}".format(rid))

    ### Update latest processed record table with record_id
    cur.execute(UPDATE_PROCESSED_RECORD, (rid,))
    print("## Updating last processed id to {}\n".format(rid))


def connect(conf):
    db = psycopg2.connect(host=conf.db_host, dbname=conf.db_name,
                          user=conf.db_user, password=conf.db_passwd)
    db.autocommit = True
    return db

# vi: ts=4 et sw=4 sts=4

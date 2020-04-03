# Copyright (C) 2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import psycopg2
from processing.main import (
    get_latest_id,
    connect,
    PROCESSED_VIEW,)


LAST_PROCESSED = """
CREATE OR REPLACE VIEW {} AS
   SELECT MAX(id) AS last_id FROM records WHERE processed = True
""".format(PROCESSED_VIEW)


class Conf():
    db_name = os.environ['POSTGRES_DB']
    db_host = os.environ['POSTGRES_HOSTNAME']
    db_user = os.environ['POSTGRES_USER']
    db_passwd = os.environ['POSTGRES_PASSWORD']


def check_processed_id(conn):
    cursor = conn.cursor()
    try:
        get_latest_id(cursor)
    except psycopg2.errors.UndefinedTable:
        cursor.execute(LAST_PROCESSED)
    finally:
        cursor.close()


def main():
    try:
        conn = connect(Conf())
        check_processed_id(conn)
        conn.close()
    except psycopg2.OperationalError as op_error:
        print("could not connect to server: Connection refused")
        exit(1)

if __name__ == '__main__':
    main()

# vi: ts=4 et sw=4 sts=4

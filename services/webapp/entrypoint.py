# Copyright (C) 2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import psycopg2

CONN = "dbname='{}' user='{}' host='{}' password='{}'"

def main():
    db_host = os.environ['POSTGRES_HOSTNAME']
    db_user = os.environ['POSTGRES_USER']
    db_passwd = os.environ['POSTGRES_PASSWORD']
    try:
        conn = psycopg2.connect(CONN.format('telemetry', db_user, db_host, db_passwd))
        conn.close()
    except psycopg2.OperationalError as op_error:
        print("could not connect to server: Connection refused")
        exit(1)

if __name__ == '__main__':
    main()

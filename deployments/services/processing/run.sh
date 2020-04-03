#!/bin/bash
# Copyright (C) 2020 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

LOG_LEVEL=${PROCESSING_LOG_LEVEL:-DEBUG}

# Wait for database to be initialized
until python3 entrypoint.py; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

# Processing loop
while true
do
    sleep 2m
    python3 process.py ProcessCrashes --local-scheduler --log-level ${LOG_LEVEL}
done

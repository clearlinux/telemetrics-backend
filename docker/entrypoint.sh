#!/bin/bash

export FLASK_APP=/var/www/telemetry/telemetryui/run.py
pushd /var/www/telemetry/telemetryui/

flask db upgrade
uwsgi --http 0.0.0.0:5000 --chdir /var/www/telemetry/telemetryui/ -w telemetryui:app \
      --spooler /var/www/telemetry/telemetryui/uwsgi-spool --py-autoreload 1

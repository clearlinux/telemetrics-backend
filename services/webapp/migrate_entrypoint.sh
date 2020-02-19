#!/bin/bash

set -e

until python3 /var/www/webapp/entrypoint.py; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

flask db upgrade

exit 0

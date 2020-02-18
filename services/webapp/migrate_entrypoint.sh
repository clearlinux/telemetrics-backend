#!/bin/bash

set -e

until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOSTNAME -U "postgres" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

flask db upgrade

exit 0

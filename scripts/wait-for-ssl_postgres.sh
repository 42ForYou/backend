#!/bin/bash

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

# 'ssl-init' 컨테이너의 작업 완료를 기다림
while [ ! -f /etc/backend/ssl/backend.crt ]; do
  echo "Waiting for ssl-init to complete..."
  sleep 1
done

>&2 echo "ssl-init is done!"

>&2 echo "Postgres is up - executing command"
exec $cmd

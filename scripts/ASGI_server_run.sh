#!/bin/bash

# Wait for the Postgres container to be ready
./scripts/wait-for-ssl_postgres.sh postgres

cd src

# Django DB 마이그레이션
python manage.py makemigrations
python manage.py migrate
python create_superuser.py

# Daphne 비동기 서버 실행
daphne -b 0.0.0.0 -e ssl:443:privateKey=/etc/backend/ssl/backend.key:certKey=/etc/backend/ssl/backend.crt pong.asgi:application
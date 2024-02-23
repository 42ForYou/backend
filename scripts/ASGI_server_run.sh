#!/bin/bash

mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 \
    -subj "/C=KR/L=Seoul/O=42Seoul/CN=nginx" \
    -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/backend.key \
    -out /etc/nginx/ssl/backend.crt;

# Wait for the Postgres container to be ready
./scripts/wait-for-postgres.sh postgres

cd src

# Django DB 마이그레이션
python manage.py makemigrations
python manage.py migrate
python create_superuser.py


# Daphne 비동기 서버 실행
daphne -b 0.0.0.0 -e ssl:443:privateKey=/etc/nginx/ssl/backend.key:certKey=/etc/nginx/ssl/backend.crt pong.asgi:application
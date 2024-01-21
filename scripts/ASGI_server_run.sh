#!/bin/bash
cd src

# Django DB 마이그레이션
python manage.py makemigrations
python manage.py migrate
# Daphne 비동기 서버 실행
daphne -b 0.0.0.0 -p 8000 pong.asgi:application

#!/bin/bash
cd src

# Django DB 마이그레이션
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --noinput --username admin --email admin@admin.com --password admin
# django dev server 실행
python manage.py runserver 0.0.0.0:8000

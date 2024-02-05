#!/bin/bash
cd src

# Django DB 마이그레이션
python manage.py makemigrations
python manage.py migrate
python create_superuser.py
# django dev server 실행
python manage.py runserver 0.0.0.0:8000

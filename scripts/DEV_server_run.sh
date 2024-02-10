#!/bin/bash

# Wait for the Postgres container to be ready
./scripts/wait-for-postgres.sh postgres

# Change directory to the source code
cd src

# Django DB 마이그레이션
python manage.py makemigrations
python manage.py migrate

# Django createsuperuser and dummy data creation
python create_superuser.py
python create_dummy_data.py

# django dev server 실행
python manage.py runserver 0.0.0.0:8000

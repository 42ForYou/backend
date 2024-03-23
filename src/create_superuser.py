# create_superuser.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")
django.setup()

from accounts.models import User


def create_superuser():
    username = "admin"
    password = "admin"
    email = "admin@admin.com"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print("Superuser created.")
    else:
        print("Superuser creation skipped: already exists.")


if __name__ == "__main__":
    create_superuser()

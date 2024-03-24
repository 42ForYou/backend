# create_superuser.py
import django

django.setup()

# pylint: disable=wrong-import-position
from accounts.models import User

# pylint: enable=wrong-import-position


def create_superuser():
    username = "admin"
    password = "42foryou"
    email = "admin@admin.com"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print("Superuser created.")
    else:
        print("Superuser creation skipped: already exists.")


if __name__ == "__main__":
    create_superuser()

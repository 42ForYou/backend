import random
import string
from django.db import models
from django.utils import timezone
from rest_framework import status
from accounts.models import User, Profile
from pong.utils import CustomError
from pong.utils import send_email
import pong.settings as settings


class OAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    access_token = models.CharField(unique=True)
    refresh_token = models.CharField(unique=True)
    token_type = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TwoFactorAuth(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="two_factor_auth"
    )
    secret_code = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_secret_code(self):
        characters = string.ascii_uppercase + string.digits
        self.secret_code = "".join(random.choice(characters) for _ in range(6))
        self.updated_at = timezone.now()
        self.save()

    def send_secret_code(self):
        self.generate_secret_code()
        send_email(
            "PlanetPong 2FA Code",
            f"Your Code is [ {self.secret_code} ]",
            settings.EMAIL_HOST_USER,
            [self.user.profile.email],
        )

    def is_valid(self, code):
        if (timezone.now() - self.updated_at).seconds > 180:
            raise CustomError(
                exception="Time out", status_code=status.HTTP_401_UNAUTHORIZED
            )
        return self.secret_code == code

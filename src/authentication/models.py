import random
import string
from django.db import models
from django.utils import timezone
from rest_framework import status
from accounts.models import User, Profile
from pong.utils import CustomError


class OAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    access_token = models.CharField(max_length=100, unique=True)
    refresh_token = models.CharField(max_length=100, unique=True)
    token_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TwoFactorAuth(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="two_factor_auth"
    )
    secret_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_secret_code(self):
        characters = string.ascii_uppercase + string.digits
        secret_code = "".join(random.choice(characters) for _ in range(6))
        return secret_code

    def save(self, *args, **kwargs):
        if not self.secret_code:
            self.secret_code = self.generate_secret_code()
        super().save(*args, **kwargs)

    def is_valid(self, code):
        if (timezone.now() - self.updated_at).seconds > 180:
            raise CustomError(
                exception="Time out", status_code=status.HTTP_401_UNAUTHORIZED
            )
        return self.secret_code == code

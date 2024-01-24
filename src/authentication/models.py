from django.db import models
from accounts.models import User, Profile


class OAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    access_token = models.CharField(max_length=100, unique=True)
    refresh_token = models.CharField(max_length=100, unique=True)
    token_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


from dataclasses import dataclass

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    intra_id = models.CharField(primary_key=True, max_length=32)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.intra_id


@dataclass
class UserDataCache:
    intra_id: str
    nickname: str
    avatar: str


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="profile"
    )
    nickname = models.CharField(
        max_length=32,
        unique=True,
    )
    email = models.EmailField(unique=True)
    avatar = models.CharField(max_length=128, default="")
    two_factor_auth = models.BooleanField(default=False)

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    intra_id = models.CharField(primary_key=True, max_length=32)

    def __str__(self):
        return self.username or self.intra_id


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    nickname = models.CharField(max_length=32, unique=True)
    email = models.CharField(max_length=128, unique=True)
    # FIXME: "profile_pics" may cause directory path issues
    image = models.ImageField(default="default.jpg", upload_to="profile_pics")

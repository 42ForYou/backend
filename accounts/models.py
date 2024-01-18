from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    intra_id = models.CharField(primary_key=True, max_length=32)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=32)
    email = models.CharField(max_length=128)
    # FIXME: "profile_pics" may cause directory path issues
    image = models.ImageField(default="default.jpg", upload_to="profile_pics")

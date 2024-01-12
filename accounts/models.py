from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    intra_id = models.CharField(primary_key=True, max_length=32)

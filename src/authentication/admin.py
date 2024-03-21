from django.contrib import admin
from .models import TwoFactorAuth, OAuth

# Register your models here.

admin.site.register(TwoFactorAuth)
admin.site.register(OAuth)

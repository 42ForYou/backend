# Generated by Django 5.0.1 on 2024-01-22 07:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0004_remove_profile_id_alter_profile_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='OAuth',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('access_token', models.CharField(max_length=100, unique=True)),
                ('refresh_token', models.CharField(max_length=100, unique=True)),
                ('token_type', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

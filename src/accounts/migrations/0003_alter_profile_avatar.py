# Generated by Django 5.0.2 on 2024-02-13 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_is_online'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.CharField(default='default-avatar.jpg', max_length=128),
        ),
    ]
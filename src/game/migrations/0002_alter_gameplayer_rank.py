# Generated by Django 5.0.2 on 2024-02-19 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameplayer',
            name='rank',
            field=models.PositiveIntegerField(default=1),
        ),
    ]

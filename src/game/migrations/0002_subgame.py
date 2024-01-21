# Generated by Django 5.0.1 on 2024-01-21 07:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveIntegerField()),
                ('idx_in_rank', models.PositiveIntegerField()),
                ('point_a', models.PositiveIntegerField(default=0)),
                ('point_b', models.PositiveIntegerField(default=0)),
                ('winner', models.CharField(max_length=1)),
                ('game_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_game', to='game.game')),
                ('player_a', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='player_a', to='game.gameplayer')),
                ('player_b', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='player_b', to='game.gameplayer')),
            ],
        ),
    ]

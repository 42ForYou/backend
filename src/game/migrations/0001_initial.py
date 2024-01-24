# Generated by Django 5.0.1 on 2024-01-24 06:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('game_id', models.AutoField(primary_key=True, serialize=False)),
                ('is_tournament', models.BooleanField(default=True)),
                ('game_point', models.PositiveIntegerField(default=1)),
                ('time_limit', models.PositiveIntegerField(default=180)),
                ('n_players', models.PositiveIntegerField(default=2)),
            ],
        ),
        migrations.CreateModel(
            name='GamePlayer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nick_name', models.CharField(default='anonymous', max_length=50)),
                ('rank', models.PositiveIntegerField(default=0)),
                ('game_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_player', to='game.game')),
                ('intra_id', models.ForeignKey(default='anonymous', on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('game_id', 'intra_id')},
            },
        ),
        migrations.CreateModel(
            name='GameRoom',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=50)),
                ('status', models.CharField(default='waiting', max_length=10)),
                ('join_players', models.PositiveIntegerField(default=0)),
                ('game_id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='game_room', to='game.game')),
                ('host', models.ForeignKey(default='anonymous', on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
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

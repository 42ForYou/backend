# Generated by Django 5.0.1 on 2024-02-05 05:41

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
                ('users', models.ManyToManyField(related_name='games', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GamePlayer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nickname', models.CharField(default='anonymous', max_length=50)),
                ('rank', models.PositiveIntegerField(default=0)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_player', to='game.game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='game_player', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('game', 'user')},
            },
        ),
        migrations.CreateModel(
            name='GameRoom',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=50)),
                ('is_playing', models.BooleanField(default=False)),
                ('join_players', models.PositiveIntegerField(default=0)),
                ('game', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='game_room', to='game.game')),
                ('host', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, related_name='game_room', to=settings.AUTH_USER_MODEL)),
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
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_game', to='game.game')),
                ('player_a', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='player_a', to='game.gameplayer')),
                ('player_b', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='player_b', to='game.gameplayer')),
            ],
        ),
    ]

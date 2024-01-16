from django.db import models


class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    is_tournament = models.BooleanField(default=True)
    game_point = models.PositiveIntegerField(default=1)
    time_limt = models.PositiveIntegerField(default=180)
    n_players = models.PositiveIntegerField(default=2)

    def __str__(self):
        return f"GameRoom {self}"


class GameRoom(models.Model):
    id = models.AutoField(primary_key=True)
    game_id = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="game_room", default=1
    )
    room_title = models.CharField(max_length=50)
    status = models.CharField(max_length=10, default="waiting")
    join_players = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"GameRoom {self}"

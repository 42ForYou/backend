from django.db import models
from accounts.models import User


class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    is_tournament = models.BooleanField(default=True)
    game_point = models.PositiveIntegerField(default=1)
    time_limt = models.PositiveIntegerField(default=180)
    n_players = models.PositiveIntegerField(default=2)

    def __str__(self):
        return f"Game {self.game_id}"


class GameRoom(models.Model):
    id = models.AutoField(primary_key=True)
    game_id = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="game_room"
    )
    title = models.CharField(max_length=50)
    status = models.CharField(max_length=10, default="waiting")
    join_players = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"GameRoom {self.game_id} of {self.title}"


class GamePlayer(models.Model):
    id = models.AutoField(primary_key=True)
    intra_id = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, default="anonymous", null=False
    )
    game_id = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="game_player", default=1
    )
    nick_name = models.CharField(max_length=50, default="anonymous")
    rank = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [["game_id", "intra_id"]]

    def __str__(self):
        return f"GamePlayer {self}"

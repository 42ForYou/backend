from django.db import models
from accounts.models import User


class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    is_tournament = models.BooleanField(default=True)
    game_point = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(default=180)
    n_players = models.PositiveIntegerField(default=2)
    users = models.ManyToManyField(User, related_name="games")

    def __str__(self):
        return f"Game {self.game_id}"


class GameRoom(models.Model):
    host = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="game_room"
    )
    game = models.OneToOneField(
        Game, on_delete=models.CASCADE, related_name="game_room"
    )
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, null=False)
    is_playing = models.BooleanField(default=False)
    join_players = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"GameRoom {self.title}"


class GamePlayer(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="game_player",
    )
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="game_player")
    nickname = models.CharField(max_length=50, default="anonymous")
    rank = models.IntegerField(
        default=-1
    )  # -1: 우승, 0: 결승에서 탈락, 1: 4강에서 탈락 ...

    class Meta:
        unique_together = [["game", "user"]]

    def __str__(self):
        return f"GamePlayer {self.nickname}"


class SubGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="sub_games")
    rank = models.PositiveIntegerField()  # 0: 결승, 1: 4강, 2: 8강 ...
    idx_in_rank = (
        models.PositiveIntegerField()
    )  # 각 "강" 내부에서의 인덱스 (0부터 시작)

    player_a = models.ForeignKey(
        GamePlayer, on_delete=models.DO_NOTHING, null=False, related_name="player_a"
    )
    player_b = models.ForeignKey(
        GamePlayer, on_delete=models.DO_NOTHING, null=False, related_name="player_b"
    )

    point_a = models.PositiveIntegerField(
        default=0
    )  # A 플레이어가 최종적으로 획득한 점수
    point_b = models.PositiveIntegerField(
        default=0
    )  # B 플레이어가 최종적으로 획득한 점수

    winner = models.CharField(max_length=1)  # "A" or "B"

    t_start = models.TimeField(auto_now=False, auto_now_add=False)
    t_end = models.TimeField(auto_now=False, auto_now_add=False)

    def __str__(self):
        return f"SubGame rank {self.rank}, [{self.idx_in_rank}] in Game {self.game_id}"

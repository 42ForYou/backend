from typing import List

from accounts.models import User
from game.models import Game, GamePlayer, SubGame
from game.serializers import GameSerializer, GamePlayerSerializer, SubGameSerializer


class GameHistory:
    def __init__(self, game: Game, game_player: GamePlayer) -> None:
        self.game = game
        self.game_player = game_player

        self.subgames: List[SubGame] = [
            subgame
            for subgame in game.sub_games.all()
            if subgame.player_a == game_player or subgame.player_b == game_player
        ]

    def serialize_subgame(self, subgame: SubGame) -> dict:
        result = SubGameSerializer(subgame).data

        result["game_player_won"] = (
            subgame.winner == "A" and subgame.player_a.id == self.game_player.id
        ) or (subgame.winner == "B" and subgame.player_b.id == self.game_player.id)

        return result

    def to_dict(self):
        return {
            "game": GameSerializer(self.game).data,
            "game_player": GamePlayerSerializer(self.game_player).data,
            "subgames": [self.serialize_subgame(subgame) for subgame in self.subgames],
        }


def get_game_histories_of_user(user: User):
    result: List[GameHistory] = []

    for game in user.games.all():
        game_player = GamePlayer.objects.filter(user=user, game=game).first()

        if not game_player:
            continue

        result.append(GameHistory(game, game_player))

    return result

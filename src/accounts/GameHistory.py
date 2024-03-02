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

    def to_dict(self):
        return {
            "game": GameSerializer(self.game).data,
            "game_player": GamePlayerSerializer(self.game_player).data,
            "subgames": [SubGameSerializer(subgame).data for subgame in self.subgames],
        }


def get_subgame_history_of_user(user: User):
    result = []

    for game in user.games.all():
        game_player = GamePlayer.objects.filter(user=user, game=game).first()

        if not game_player:
            continue

        result.append(GameHistory(game, game_player).to_dict())

    return result

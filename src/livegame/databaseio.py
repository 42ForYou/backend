import time
import random
import logging

from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from game.models import GamePlayer, Game, GameRoom
from game.serializers import GamePlayerSerializer, GameSerializer, GameRoomSerializer


logger = logging.getLogger(f"{__package__}.{__name__}")


@sync_to_async
def left_game_room(game_room_id, player_id):
    try:
        game_room = GameRoom.objects.prefetch_related(
            Prefetch(
                "game__game_player",
                queryset=GamePlayer.objects.order_by("id"),
                to_attr="ordered_players",
            )
        ).get(id=game_room_id)
        player = GamePlayer.objects.select_related("user__socket_session").get(
            id=player_id
        )
    except (GameRoom.DoesNotExist, GamePlayer.DoesNotExist) as e:
        logger.error(f"Error in left_game_room: {e}")
        return None, None, None

    game = game_room.game
    ordered_players = getattr(game, "ordered_players", None)

    if game_room.host == player.user:
        game.delete()
        unix_time = time.time()
        data = {"t_event": unix_time, "destroyed_because": "host_left"}
        return data, None, None

    ordered_players.remove(player)
    player.delete()

    sid_list = [
        player.user.socket_session.game_room_session_id for player in ordered_players
    ]
    player_id_list = [player.id for player in ordered_players if player.id != player_id]
    am_i_host_list = [player.user == game_room.host for player in ordered_players]

    data = serialize_game_data(game, game_room, ordered_players)

    return data, player_id_list, sid_list, am_i_host_list


def serialize_game_data(game, game_room, players):
    game_serializer = GameSerializer(game)
    game_room_serializer = GameRoomSerializer(game_room)
    players_serializer = GamePlayerSerializer(players, many=True)
    return {
        "game": game_serializer.data,
        "room": game_room_serializer.data,
        "players": players_serializer.data,
    }

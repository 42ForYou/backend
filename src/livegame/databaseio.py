import time
import logging

from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from game.models import GamePlayer, GameRoom
from game.serializers import GamePlayerSerializer, GameSerializer, GameRoomSerializer


logger = logging.getLogger(f"{__package__}.{__name__}")


@sync_to_async
def left_game_room(game_room_id, intra_id):
    try:
        game_room = GameRoom.objects.prefetch_related(
            Prefetch(
                "game__game_player",
                queryset=GamePlayer.objects.order_by("id"),
                to_attr="ordered_players",
            )
        ).get(id=game_room_id)
        logger.debug(f"Player {intra_id} left the game room {game_room_id}")
        player = GamePlayer.objects.get(game=game_room.game, user=intra_id)
    except (GameRoom.DoesNotExist, GamePlayer.DoesNotExist) as e:
        logger.error(f"Error in left_game_room: {e}")
        return None, None, None, None

    game = game_room.game
    players = getattr(game, "ordered_players", None)

    if game_room.host == player.user:
        logger.debug(f"Host left the game room {game_room_id}")
        game.delete()
        unix_time = time.time()
        data = {"t_event": unix_time, "destroyed_because": "host_left"}
        return data, None, None, None

    players.remove(player)
    player.delete()
    game_room.join_players -= 1
    game_room.save()

    data, sid_list, player_id_list, am_i_host_list = get_data_and_lists_for_update_room(
        game, game_room, players
    )

    return data, player_id_list, sid_list, am_i_host_list


@sync_to_async
def get_room_data(game_room_id):
    try:
        game_room = GameRoom.objects.prefetch_related(
            Prefetch(
                "game__game_player",
                queryset=GamePlayer.objects.order_by("id"),
                to_attr="ordered_players",
            )
        ).get(id=game_room_id)
    except (GameRoom.DoesNotExist, GamePlayer.DoesNotExist) as e:
        logger.error(f"Error in get_room_data: {e}")
        return None, None, None, None

    game = game_room.game
    players = getattr(game, "ordered_players", None)
    data, sid_list, player_id_list, am_i_host_list = get_data_and_lists_for_update_room(
        game, game_room, players
    )

    return data, sid_list, player_id_list, am_i_host_list


def get_data_and_lists_for_update_room(game, game_room, players):
    try:
        data = serialize_game_data(game, game_room, players)
        player_id_list = [player.id for player in players]
        sid_list = [
            player.user.socket_session.game_room_session_id for player in players
        ]
        am_i_host_list = [player.user == game_room.host for player in players]
    except Exception as e:
        logger.error(f"Error in get_data_and_lists_for_update_room: {e}")
        return None, None, None, None

    return data, sid_list, player_id_list, am_i_host_list


def serialize_game_data(game, game_room, players):
    game_serializer = GameSerializer(game)
    game_room_serializer = GameRoomSerializer(game_room)
    players_serializer = GamePlayerSerializer(players, many=True)
    return {
        "game": game_serializer.data,
        "room": game_room_serializer.data,
        "players": players_serializer.data,
    }

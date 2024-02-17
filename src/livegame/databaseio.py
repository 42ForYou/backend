import time
import random
from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from game.models import GamePlayer, Game, GameRoom
from game.serializers import GamePlayerSerializer, GameSerializer, GameRoomSerializer


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
        print(f"Error in left_game_room: {e}")
        return None, None, None

    game = game_room.game
    oredred_players = getattr(game, "ordered_players", None)

    if game_room.host == player.user:
        game.delete()
        unix_time = time.time()
        data = {"t_event": unix_time, "destroyed_because": "host_left"}
        return data, None, None

    data = serialize_game_data(game, game_room, oredred_players)

    if not game_room.is_playing:
        updated_players, sid_list = update_game_room_for_leaving_player(
            game_room, player, oredred_players
        )
        data["players"] = updated_players
    else:
        sid_list = [
            player.user.socket_session.game_room_session_id
            for player in oredred_players
        ]
    player_id_list = [player.id for player in oredred_players if player.id != player_id]

    return data, player_id_list, sid_list


def serialize_game_data(game, game_room, players):
    game_serializer = GameSerializer(game)
    game_room_serializer = GameRoomSerializer(game_room)
    players_serializer = GamePlayerSerializer(players, many=True)
    return {
        "game": game_serializer.data,
        "room": game_room_serializer.data,
        "players": players_serializer.data,
    }


def update_game_room_for_leaving_player(game_room, leaving_player, players):
    players = [player for player in players if player.id != leaving_player.id]
    sid_list = [player.user.socket_session.game_room_session_id for player in players]
    leaving_player.delete()
    game_room.join_players -= 1
    game_room.save()
    serialized_players = GamePlayerSerializer(players, many=True).data
    return serialized_players, sid_list


@sync_to_async
def game_start(game_room_id):
    game_room = GameRoom.objects.get(pk=game_room_id)
    game_room.is_playing = True
    game_room.save()


@sync_to_async
def update_or_create_matchs_list(match_dict, game_room_id):
    if not match_dict:
        game_room = GameRoom.objects.get(pk=game_room_id)
        game = game_room.game
        players = game.game_player.all().order_by("id")
        unix_time = time.time()
        data = {
            "t_event": unix_time,
            "n_ranks": int(len(players) / 2),
            "rank_ongoing": 1,
        }
        players_list = list(players)
        random.shuffle(players_list)
        players_serializer = GamePlayerSerializer(players_list, many=True)
        players_data = [[None, None], [players_data[:2], players_data[2:]]]
        data.update({"players": players_data})
        return data
    else:
        return match_dict

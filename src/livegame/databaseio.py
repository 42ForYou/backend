import time
import random
from asgiref.sync import sync_to_async
from game.models import GamePlayer, Game, GameRoom
from game.serializers import GamePlayerSerializer, GameSerializer, GameRoomSerializer


@sync_to_async
def left_game_room(game_room_id, player_id):
    game_room = GameRoom.objects.get(pk=game_room_id)
    player = GamePlayer.objects.get(pk=player_id)
    game = game_room.game
    if game_room.host == player.user:
        game.delete()
        unix_time = time.time()
        data = {"t_event": unix_time, "destroyed_because": "host_left"}
        return data, None, None
    players = game.game_player.all().order_by("id")
    players_serializer = GamePlayerSerializer(players, many=True)
    game_serializer = GameSerializer(game)
    game_room_serializer = GameRoomSerializer(game_room)
    data = {
        "game": game_serializer.data,
        "room": game_room_serializer.data,
        "players": players_serializer.data,
    }
    player_id_list = [player.id for player in players]
    sid_list = [player.user.socket_session.session_id for player in players]
    if game_room.is_playing == False:
        player_id_list.remove(player.id)
        sid_list.remove(player.socket_session.session_id)
        player.delete()
        game_room.join_players -= 1
        game_room.save()
    return data, player_id_list, sid_list


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

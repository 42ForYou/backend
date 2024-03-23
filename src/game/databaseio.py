from .models import GameRoom, GamePlayer
from .serializers import GameRoomSerializer, GameSerializer, GamePlayerSerializer
from pong.utils import CustomError
from rest_framework import status


def get_single_game_room(game_room_id):
    try:
        game_room = GameRoom.objects.get(id=game_room_id)
        game = game_room.game
        game_serializer = GameSerializer(game)
        game_room_serializer = GameRoomSerializer(game_room)
        data = {"game": game_serializer.data, "room": game_room_serializer.data}
        players = game.game_player.all().order_by("id")
        data.update({"players": GamePlayerSerializer(players, many=True).data})
        return data
    except Exception as e:
        raise CustomError(e, "game_room", status_code=status.HTTP_400_BAD_REQUEST)


def create_game(user, game_data):
    try:
        if GamePlayer.objects.filter(
            user=user, game__game_room__is_playing=False
        ).exists():
            raise CustomError(
                "You are already in a game room",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer = GameSerializer(data=game_data)
        serializer.is_valid(raise_exception=True)
        game = serializer.save()
        return game
    except Exception as e:
        raise CustomError(e, status_code=status.HTTP_400_BAD_REQUEST)

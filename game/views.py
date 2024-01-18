from rest_framework.views import APIView
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from asgiref.sync import sync_to_async
from rest_framework.response import Response

from rest_framework import status

from .models import Game, GameRoom, GamePlayer, User
from .serializers import (
    GameSerializer,
    GameRoomSerializer,
    GameRoomJoinSerializer,
    GamePlayerSerializer,
)


def get_game_room(game_id):
    try:
        return GameRoom.objects.get(game_id=game_id)
    except GameRoom.DoesNotExist:
        return None


def delete_game_room(game_room):
    print("delete_game_room")
    if game_room.status == "waiting":
        try:
            game = game_room.game_id
            game.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Game.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    game_room.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def is_authorized_user(request):
    return request.user.intra_id == request.data["intra_id"]


def wrap_data(serializer):
    return {"data": serializer.data}


@sync_to_async
@api_view(["GET", "POST", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def game_rooms_view(request, game_id=None):
    if request.method == "GET":
        if game_id:
            try:
                game_room = GameRoom.objects.select_related("game_id").get(pk=game_id)
                serializer = GameRoomJoinSerializer(game_room)
            except GameRoom.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            game_rooms = GameRoom.objects.select_related("game_id").all()
            serializer = GameRoomJoinSerializer(game_rooms, many=True)
        return Response(wrap_data(serializer), status=status.HTTP_200_OK)

    elif request.method == "POST":
        if game_id:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return create_game_room(request)

    elif request.method == "DELETE":
        if not game_id:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        game_room = get_game_room(game_id)
        if not game_room:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return delete_game_room(game_room)


def create_game_room(request):
    game_serializer = GameSerializer(data=request.data)
    if game_serializer.is_valid():
        game = game_serializer.save()
        game_room_data = request.data.copy()["room"]
        game_room_data["game_id"] = game.game_id
        game_room_serializer = GameRoomSerializer(data=game_room_data)
        if game_room_serializer.is_valid():
            game_room_serializer.save()
            return Response(
                wrap_data(game_room_serializer), status=status.HTTP_201_CREATED
            )
        return Response(game_room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(game_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def is_authorized(requsest):
    intra_id = requsest.data["intra_id"]
    if requsest.user.intra_id == intra_id:
        return True
    return False


@sync_to_async
@api_view(["GET", "POST", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def players_view(request):
    game_id = request.data["game_id"]
    if not game_id:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    if request.method == "GET":
        try:
            players = GamePlayer.objects.select_related("game_id").filter(
                game_id=game_id
            )
            serializer = GamePlayerSerializer(players, many=True)
            return Response(wrap_data(serializer), status=status.HTTP_200_OK)
        except GamePlayer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    elif request.method == "POST":
        serializer = GamePlayerSerializer(data=request.data)
        if serializer.is_valid():
            game_room = GameRoom.objects.get(game_id=game_id)
            if (
                game_room.status == "waiting"
                and game_room.join_players < game_room.game_id.n_players
                and is_authorized(request)
            ):
                serializer.save()
                game_room.join_players += 1
                game_room.save()
                return Response(wrap_data(serializer), status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        try:
            game_room = get_game_room(game_id=game_id)
            if game_room and game_room.status == "waiting":
                if is_authorized(request):
                    player = GamePlayer.objects.get(
                        game_id=game_id, intra_id=request.data["intra_id"]
                    )
                    player.delete()
                    game_room.join_players -= 1
                    if game_room.join_players == 0:
                        return delete_game_room(game_room)
                    game_room.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except GamePlayer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

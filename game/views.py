from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from asgiref.sync import sync_to_async
from rest_framework.response import Response

from rest_framework import status
from django.http import Http404

from .models import Game, GameRoom, GamePlayer, User
from .serializers import *


def get_game_room(id):
    try:
        return GameRoom.objects.get(id=id)
    except GameRoom.DoesNotExist:
        return None


def delete_game_room(game_room):
    if game_room.status == "waiting":
        try:
            game = game_room.game_id
            game.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Game.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    game_room.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def join_host(request, game_room):
    host = game_room.host
    game = game_room.game_id
    game_player = GamePlayer(intra_id=host, game_id=game, rank=0)
    game_player.save()


def is_authorized_user(request):
    return request.user.intra_id == request.data["intra_id"]


class GameRoomViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GameRoom.objects.all()
    serializer_class = GameRoomSerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

    def list(self, request):
        game_rooms = GameRoom.objects.all()
        serializer = GameRoomSerializer(game_rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        try:
            game_room = GameRoom.objects.select_related("game_id").get(pk=kwargs["pk"])
            serializer = GameRoomSerializer(game_room)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except GameRoom.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        serializer = GameRoomSerializer(data=request.data)
        if serializer.is_valid():
            game_room = serializer.save()
            join_host(request, game_room)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        if not kwargs.get("pk"):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        game_room = get_game_room(kwargs["pk"])
        if not game_room:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return delete_game_room(game_room)


class PlayerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GamePlayer.objects.all()
    serializer_class = GamePlayerSerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

    def list(self, request):
        try:
            players = GamePlayer.objects.all()
            serializer = GamePlayerSerializer(players, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except GamePlayer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        game_id = kwargs["pk"]
        if not game_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = GamePlayerSerializer(data=request.data)
        if serializer.is_valid():
            game_room = GameRoom.objects.get(game_id=game_id)
            if (
                game_room.status == "waiting"
                and game_room.join_players < game_room.game_id.n_players
            ):
                serializer.save()
                game_room.join_players += 1
                game_room.save()
                return Response((serializer), status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        game_id = kwargs["pk"]
        intra_id = request.query_params["intra_id"]
        if not game_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            game_room = get_game_room(game_id=game_id)
            print(game_room)
            if game_room and game_room.status == "waiting":
                print(request.data)
                player = GamePlayer.objects.get(game_id=game_id, intra_id=intra_id)
                player.delete()
                game_room.join_players -= 1
                if game_room.join_players == 0:
                    return delete_game_room(game_room)
                game_room.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        except GamePlayer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

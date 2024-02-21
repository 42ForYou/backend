import time
import asyncio

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Game, GameRoom, GamePlayer, SubGame
from .serializers import *
from pong.utils import (
    CustomError,
    CookieTokenAuthentication,
    wrap_data,
    CustomPageNumberPagination,
)
from .databaseio import get_single_game_room, create_game
from socketcontrol.events import sio
from livegame.GameRoomSession import (
    GameRoomSession,
    GAMEROOMSESSION_REGISTRY,
)


def get_game_room(id):
    try:
        return GameRoom.objects.get(id=id)
    except GameRoom.DoesNotExist:
        return None


def delete_game_room(game_room):
    try:
        if game_room.is_playing == False:
            game = game_room.game
            game.delete()
        else:
            game_room.delete()
    except Exception as e:
        raise CustomError(e, status_code=status.HTTP_400_BAD_REQUEST)


class IsPlayerInGameRoom(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.game.game_player.filter(user=request.user).exists()


class GameRoomViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GameRoom.objects.all()
    serializer_class = GameRoomSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsPlayerInGameRoom]
    pagination_class = CustomPageNumberPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "is_tournament",
                openapi.IN_QUERY,
                description="Filter game rooms by tournament status",
                type=openapi.TYPE_BOOLEAN,
            )
        ],
        responses={200: SwaggerGameListSerializer(many=True)},
    )
    def list(self, request):
        try:
            paginator = CustomPageNumberPagination()
            filter = request.query_params.get("filter", None)
            if filter:
                if filter not in ["tournament", "dual"]:
                    raise CustomError(
                        exception='Invalid filter value. Expected "tournament" or "dual"',
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                is_tournament = False
                if filter == "tournament":
                    is_tournament = True
                game_rooms = GameRoom.objects.filter(
                    game__is_tournament=is_tournament
                ).order_by("id")
            else:
                game_rooms = GameRoom.objects.all().order_by("id")
            context = paginator.paginate_queryset(game_rooms, request)
            data = []
            for game_room in context:
                game_room_serializer = GameRoomSerializer(game_room)
                game_serializer = GameSerializer(game_room.game)
                players = game_room.game.game_player.all().order_by("id")
                players_serializer = GamePlayerSerializer(players, many=True)
                data.append(
                    {
                        "game": game_serializer.data,
                        "room": game_room_serializer.data,
                        "players": players_serializer.data,
                    }
                )
            return paginator.get_paginated_response(data)
        except Exception as e:
            raise CustomError(e, "game_room", status_code=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={200: SwaggerGameRetriveSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            room_id = kwargs["pk"]
            game_room = GameRoom.objects.get(id=room_id)
            self.check_object_permissions(request, game_room)
            data = get_single_game_room(room_id)
            my_player_id = game_room.game.game_player.get(user=request.auth.user).id
            data["my_player_id"] = my_player_id
            return Response({"data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(e, "game_room", status_code=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        game = None
        try:
            request_data = request.data.get("data")
            game = create_game(request_data.get("game"))
            game_room = self.create_room(request, request_data, game)
            GAMEROOMSESSION_REGISTRY[game_room.id] = GameRoomSession(game)
            sio.register_namespace(GAMEROOMSESSION_REGISTRY[game_room.id])
            player = self.join_host(game_room)
            data = self.serialize_game_and_room(game, game_room)
            data.update({"players": [GamePlayerSerializer(player).data]})
            data.update({"my_player_id": player.id})
            data.update({"am_i_host": True})
            return Response(
                {"data": data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            if game:
                game.delete()
            raise CustomError(e, "game_room", status_code=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        if not kwargs.get("pk"):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        game_room = get_game_room(kwargs["pk"])
        if not game_room:
            return Response(status=status.HTTP_404_NOT_FOUND)
        delete_game_room(game_room)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create_room(self, request, request_data, game):
        try:
            room_data = request_data.get("room")
            room_data["game"] = game.game_id
            user = request.auth.user
            room_data["host"] = user.intra_id
            serializer = GameRoomSerializer(data=room_data)
            serializer.is_valid(raise_exception=True)
            game_room = serializer.save()
            return game_room
        except Exception as e:
            raise CustomError(e, status_code=status.HTTP_400_BAD_REQUEST)

    def join_host(self, game_room):
        try:
            host = game_room.host
            game = game_room.game
            player_data = {"user": host, "game": game.game_id}
            serializer = GamePlayerSerializer(data=player_data)
            serializer.is_valid(raise_exception=True)
            player = serializer.save()
            game_room.join_players += 1
            game_room.save()
            return player
        except Exception as e:
            raise CustomError(e, status_code=status.HTTP_400_BAD_REQUEST)

    def serialize_game_and_room(self, game, room):
        game_serializer = GameSerializer(game)
        room_serializer = GameRoomSerializer(room)
        return {"game": game_serializer.data, "room": room_serializer.data}


class PlayerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GamePlayer.objects.all()
    serializer_class = GamePlayerSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "game_id",
                openapi.IN_PATH,
                description="ID of the game",
                type=openapi.TYPE_INTEGER,
            )
        ],
        responses={200: GamePlayerSerializer(many=True)},
    )
    def list(self, request, game_id=None):
        try:
            game_id = request.query_params.get("game_id", None)
            if not game_id:
                raise CustomError(
                    "game_id query string is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            players = GamePlayer.objects.filter(game=game_id).order_by("id")
            serializer = GamePlayerSerializer(players, many=True)
            return Response(
                wrap_data(players=serializer.data), status=status.HTTP_200_OK
            )
        except Exception as e:
            raise CustomError(e, "game_player", status_code=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            player_id = kwargs["pk"]
            player = GamePlayer.objects.get(pk=player_id)
            serializer = GamePlayerSerializer(player)
            return Response(
                wrap_data(player=serializer.data), status=status.HTTP_200_OK
            )
        except Exception as e:
            raise CustomError(e, "game_player", status_code=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            game_id = request.data.get("data").get("game_id")
            if not game_id:
                raise CustomError(
                    "game_id is required", status_code=status.HTTP_400_BAD_REQUEST
                )
            game = Game.objects.get(game_id=game_id)
            game_room = game.game_room
            if game.n_players == game_room.join_players:
                raise CustomError(
                    "The game room is full",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if game_room.is_playing == True:
                raise CustomError(
                    "The game room is already started",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if self.user_already_in_game_room(request.auth.user, game):
                raise CustomError(
                    "The user is already participating",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            user = request.auth.user
            request.data["game"] = game_id
            request.data["user"] = user.intra_id
            serializer = GamePlayerSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            game_room.join_players += 1
            game_room.save()
            players = game.game_player.all().order_by("id")
            my_player_id = game.game_player.get(user=user).id
            players_serializer = GamePlayerSerializer(players, many=True)
            game_serializer = GameSerializer(game)
            game_room_serializer = GameRoomSerializer(game_room)
            my_player_id = game.game_player.get(user=user).id

            game_room_ns = GAMEROOMSESSION_REGISTRY[game_room.id]
            data = {
                "game": game_serializer.data,
                "room": game_room_serializer.data,
                "players": players_serializer.data,
            }
            player_id_list = [player.id for player in players]
            sid_list = [
                player.user.socket_session.game_room_session_id for player in players
            ]
            am_i_host_list = [player.user == game_room.host for player in players]
            asyncio.run(game_room_ns.emit_update_room(data, player_id_list, sid_list, am_i_host_list))

            return Response(
                wrap_data(
                    game=game_serializer.data,
                    room=game_room_serializer.data,
                    players=players_serializer.data,
                    my_player_id=my_player_id,
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            if isinstance(e, serializers.ValidationError):
                raise CustomError(
                    "The player is already participating",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            raise CustomError(e, "game", status_code=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            player_id = kwargs["pk"]
            user = request.auth.user
            if not player_id:
                raise CustomError(
                    "player_id is required", status_code=status.HTTP_400_BAD_REQUEST
                )
            player = GamePlayer.objects.get(pk=player_id)
            if player.user != user:
                raise CustomError(
                    "You are not the user of the player",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            game = player.game
            game_room = game.game_room
            if game_room.host == player.user:
                game.delete()
                game_room_ns = GAMEROOMSESSION_REGISTRY[game_room.id]
                asyncio.run(game_room_ns.emit_destroyed("host_left"))
                return Response(
                    {"message": "The host left the game room"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            if game_room.is_playing == False:
                player = GamePlayer.objects.get(game=game, user=user)
                player.delete()
                game_room.join_players -= 1
                if game_room.join_players == 0:
                    delete_game_room(game_room)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                game_room.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise CustomError(
                    "The game is already started",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            raise CustomError(e, "game room", status_code=status.HTTP_400_BAD_REQUEST)

    def user_already_in_game_room(self, user, game):
        if (
            GamePlayer.objects.filter(
                user=user, game__game_room__is_playing=False
            ).exists()
            or GamePlayer.objects.filter(user=user, game=game).exists()
        ):
            return True
        return False


class SubGameViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = SubGame.objects.all()
    serializer_class = SubGameSerializer


# class GameResultViewSet(
#     mixins.CreateModelMixin,
#     mixins.RetrieveModelMixin,
#     mixins.ListModelMixin,
#     viewsets.GenericViewSet,
# ):
#     queryset = GameResult.objects.all()
#     serializer_class = GameResultSerializer


# class GameResultEntryViewSet(
#     mixins.CreateModelMixin,
#     mixins.RetrieveModelMixin,
#     mixins.ListModelMixin,
#     viewsets.GenericViewSet,
# ):
#     queryset = GameResultEntry.objects.all()
#     serializer_class = GameResultEntrySerializer

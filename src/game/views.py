from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import mixins
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

from asgiref.sync import sync_to_async
from rest_framework.response import Response

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import AuthenticationFailed


from .models import Game, GameRoom, GamePlayer, SubGame
from .serializers import *


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "data": data,
                "pages": {
                    "total_pages": self.page.paginator.num_pages,
                    "count": self.page.paginator.count,
                    "current_page": self.page.number,
                    "previous_page": self.get_previous_link(),
                    "next_page": self.get_next_link(),
                },
            },
            status=status.HTTP_200_OK,
        )


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
    if game_player:
        game_player.save()
        game_room.join_players += 1
    else:
        game.delete()


class GameRoomViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GameRoom.objects.all()
    serializer_class = GameRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = PageNumberPagination

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
        paginator = CustomPageNumberPagination()
        is_tournament = request.query_params.get("is_tournament", None)
        if is_tournament:
            is_tournament = is_tournament == "true"
            game_rooms = GameRoom.objects.filter(game_id__is_tournament=is_tournament)
        else:
            game_rooms = GameRoom.objects.all()
        context = paginator.paginate_queryset(game_rooms, request)
        data = []
        for game_room in context:
            game_room_serializer = GameRoomSerializer(game_room)
            game_serializer = GameSerializer(game_room.game_id)
            data.append(
                {"game": game_serializer.data, "room": game_room_serializer.data}
            )
        return paginator.get_paginated_response(data)

    @swagger_auto_schema(
        responses={200: SwaggerGameRetriveSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            game_room = GameRoom.objects.select_related("game_id").get(pk=kwargs["pk"])
            data = self.serialize_game_and_room(game_room.game_id, game_room)
            return Response({"data": data}, status=status.HTTP_200_OK)
        except GameRoom.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        try:
            request_data = request.data.get("data")
            game = self.create_game(request_data)
            room = self.create_room(request, request_data, game)
            join_host(request, room)
            data = self.serialize_game_and_room(game, room)
            return Response(
                {"data": data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        if not kwargs.get("pk"):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        game_room = get_game_room(kwargs["pk"])
        if not game_room:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return delete_game_room(game_room)

    def create_game(self, request_data):
        serializer = GameSerializer(data=request_data.get("game"))
        if serializer.is_valid():
            game = serializer.save()
            return game
        return None

    # request.user가 host인 GameRoom을 생성해야함(테스트 불가)
    def create_room(self, request, request_data, game):
        room_data = request_data.get("room")
        room_data["game_id"] = game.game_id

        token = request.META.get("HTTP_AUTHORIZATION", None)
        user = Token.objects.get(key=token.split(" ")[1]).user
        room_data["host"] = user.intra_id
        serializer = GameRoomSerializer(data=room_data)
        if serializer.is_valid():
            game_room = serializer.save()
            return game_room
        else:
            game.delete()
            return None

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
    authentication_classes = [TokenAuthentication]

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


class SubGameViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = SubGame.objects.all()
    serializer_class = SubGameSerializer


class GameResultViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GameResult.objects.all()
    serializer_class = GameResultSerializer


class GameResultEntryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GameResultEntry.objects.all()
    serializer_class = GameResultEntrySerializer

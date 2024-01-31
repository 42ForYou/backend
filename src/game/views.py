from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from rest_framework import mixins
from rest_framework import permissions

from rest_framework.response import Response

from rest_framework import status
from rest_framework.pagination import PageNumberPagination


from .models import Game, GameRoom, GamePlayer, SubGame
from .serializers import *
from pong.utils import CustomError, CookieTokenAuthentication


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
    try:
        if game_room.status == "waiting":
            game = game_room.game
            game.delete()
        else:
            game_room.delete()
    except Exception as e:
        raise CustomError(e, status_code=status.HTTP_400_BAD_REQUEST)


class GameRoomViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = GameRoom.objects.all()
    serializer_class = GameRoomSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
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
        try:
            paginator = CustomPageNumberPagination()
            is_tournament = request.query_params.get("is_tournament", None)
            if is_tournament:
                is_tournament = is_tournament == "true"
                game_rooms = GameRoom.objects.filter(game__is_tournament=is_tournament)
            else:
                game_rooms = GameRoom.objects.all()
            context = paginator.paginate_queryset(game_rooms, request)
            data = []
            for game_room in context:
                game_room_serializer = GameRoomSerializer(game_room)
                game_serializer = GameSerializer(game_room.game)
                data.append(
                    {"game": game_serializer.data, "room": game_room_serializer.data}
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
            data = self.serialize_game_and_room(game_room.game, game_room)
            return Response({"data": data}, status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(e, "game_room", status_code=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            request_data = request.data.get("data")
            game = self.create_game(request_data)
            game_room = self.create_room(request, request_data, game)
            self.join_host(game_room)
            data = self.serialize_game_and_room(game, game_room)
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
        return delete_game_room(game_room)


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
            players = GamePlayer.objects.filter(game=game_id)
            serializer = GamePlayerSerializer(players, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(e, "game_player", status_code=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            game_id = request.data.get("game_id")
            game = Game.objects.get(game_id=game_id)
            game_room = game.game_room
            if not game_id:
                raise CustomError(
                    "game_id is required", status_code=status.HTTP_400_BAD_REQUEST
                )
            if (
                game.n_players == game_room.join_players
                or game_room.status == "playing"
            ):
                raise CustomError("Can't join", status_code=status.HTTP_400_BAD_REQUEST)
            user = request.auth.user
            request.data["game"] = game_id
            request.data["user"] = user.intra_id
            serializer = GamePlayerSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            game_room.join_players += 1
            game_room.save()
            return Response((serializer), status_code=status.HTTP_201_CREATED)
        except Exception as e:
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
            game = player.game
            game_room = game.game_room
            if game_room.status == "waiting":
                player = GamePlayer.objects.get(game=game, user=user)
                player.delete()
                game_room.join_players -= 1
                if game_room.join_players == 0:
                    delete_game_room(game_room)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                game_room.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise CustomError(e, "game room", status_code=status.HTTP_400_BAD_REQUEST)


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

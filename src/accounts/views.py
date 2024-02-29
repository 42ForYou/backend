from rest_framework import mixins, viewsets
from .models import Profile
from friends.models import Friend
from django.db.models import Q
from .serializers import (
    ProfileSerializer,
    ProfileNotOwnerSerializer,
    ProfileResponseSerializer,
    DataWrapperSerializer,
    WrapDataSwaggerProfileSerializer,
    WrapDataSwaggerOnlyProfileSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from pong.utils import CookieTokenAuthentication, CustomError, wrap_data
import hashlib
import os
import logging
import math
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, JSONParser
import json
import pong.settings as settings
from datetime import datetime
from pong.utils import CustomPageNumberPagination
from game.models import Game, GamePlayer, SubGame
from game.serializers import GameSerializer, GamePlayerSerializer, SubGameSerializer
from accounts.models import User


logger = logging.getLogger(f"{__package__}.{__name__}")


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user.intra_id == request.user.intra_id


class ProfileViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    parser_classes = [MultiPartParser, JSONParser]
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    lookup_field = "user__intra_id"
    lookup_url_kwarg = "intra_id"
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @swagger_auto_schema(
        responses={200: WrapDataSwaggerProfileSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            if request.user.intra_id != kwargs["intra_id"]:
                instance = Profile.objects.get(user=kwargs["intra_id"])
                serializer = ProfileNotOwnerSerializer(instance)
                friend_relation = Friend.objects.filter(
                    (
                        Q(requester=request.user, receiver=instance.user)
                        | Q(requester=instance.user, receiver=request.user)
                    ),
                    status__in=[
                        "pending",
                        "friend",
                    ],
                ).first()
                friend_status = friend_relation.status if friend_relation else "None"
                response_data = serializer.data
                response_data.update(
                    {"friend_id": friend_relation.id if friend_relation else None}
                )
                response_data.update({"friend_status": friend_status})
            else:
                instance = self.get_object()
                response_data = ProfileSerializer(instance).data
            return Response(
                wrap_data(user=response_data, match_history=[{}]),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=WrapDataSwaggerOnlyProfileSerializer(),
        responses={200: WrapDataSwaggerOnlyProfileSerializer()},
    )
    def update(self, request, *args, **kwargs):
        try:
            user = request.user
            profile = user.profile
            serializer_data = request.data
            if "image" in request.FILES:
                image_obj = request.FILES["image"]
                image_name = self.save_image(image_obj, user.intra_id, profile)
                profile.avatar = image_name
                profile.save()
            if "data" in request.data:
                additional_data = json.loads(request.data.get("data"))
                serializer_data = {**serializer_data, **additional_data}
                serializer_data.pop("data", None)
                instance = self.get_object()
                serializer = self.get_serializer(
                    instance, data=serializer_data, partial=True
                )
                serializer.validate(serializer_data)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
            instance = self.get_object()
            serializer = ProfileSerializer(instance)
            return Response(
                DataWrapperSerializer(
                    {"user": serializer.data, "match_history": [{}]},
                    inner_serializer=ProfileResponseSerializer,
                ).data,
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError as e:
            raise CustomError(e.detail, status_code=status.HTTP_409_CONFLICT)
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)

    def save_image(self, image_obj, intra_id, profile):
        extension = self.get_extension(image_obj.content_type)
        if not extension:
            raise CustomError(
                exception="Invalid image type",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        current_time = datetime.now().isoformat()
        hashed_filename = (
            hashlib.sha256((intra_id + current_time).encode("utf-8")).hexdigest()
            + extension
        )
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, settings.AVATAR_LOCATION, hashed_filename)

        if profile.avatar and profile.avatar != "":
            pre_file_path = os.path.join(
                base_dir, settings.AVATAR_LOCATION, profile.avatar
            )
            if default_storage.exists(pre_file_path):
                default_storage.delete(pre_file_path)

        default_storage.save(file_path, image_obj)

        return hashed_filename

    def get_extension(self, content_type):
        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
        }

        return extensions[content_type]


class UserSearchViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileNotOwnerSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            paginator = CustomPageNumberPagination()
            query = request.query_params.get("search")
            if not query:
                empty_queryset = self.queryset.none()
                page = paginator.paginate_queryset(empty_queryset, request)
                return paginator.get_paginated_response(page)
            filtered_queryset = self.queryset.filter(nickname__icontains=query)
            page = paginator.paginate_queryset(filtered_queryset, request)
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)


def get_subgame_history_of_user(user: User):
    result = []

    for game in user.games.all():
        game_player = GamePlayer.objects.filter(user=user, game=game).first()

        if not game_player:
            continue

        result.append({})

        result[-1]["game"] = GameSerializer(game).data
        result[-1]["game_player"] = GamePlayerSerializer(game_player).data

        all_sub_games = game.sub_games.all()
        result[-1]["subgames"] = []

        for sub_game in all_sub_games:
            if not (
                sub_game.player_a == game_player or sub_game.player_b == game_player
            ):
                continue

            result[-1]["subgames"].append(SubGameSerializer(sub_game).data)

    return result


def subgame_history_to_stats(history):
    result = {
        "n_dual_match": 0,  # 총 1대1 대전 횟수
        "n_dual_wins": 0,  # 1대1 대전 승리 횟수
        "n_dual_looses": 0,  # 1대1 대전 패배 횟수
        "n_tournaments": 0,  # 토너먼트 참가 횟수
        "tournament_stats": [],  # 토너먼트 기록
    }

    def find_tournament_stat(n_players):
        n_ranks = int(math.log2(n_players))
        for stat in result["tournament_stats"]:
            if stat["n_ranks"] == n_ranks:
                return stat

        result["tournament_stats"].append(
            {
                "n_ranks": n_ranks,
                "n_plays": 0,
                "stats": [
                    {"final_rank": i, "n_tournaments": 0} for i in range(-1, n_ranks)
                ],
            }
        )
        return result["tournament_stats"][-1]

    def find_final_rank_stat(tournament_stat: dict, final_rank):
        for rank_data in tournament_stat["stats"]:
            if rank_data["final_rank"] == final_rank:
                return rank_data
        raise Exception(f"{final_rank} not found in {tournament_stat}")

    for game_history in history:
        game = game_history["game"]
        player = game_history["game_player"]
        player_id = player["id"]
        subgames = game_history["subgames"]

        if game["is_tournament"]:
            result["n_tournaments"] += 1
            tournament_stat = find_tournament_stat(game["n_players"])
            final_rank_stat = find_final_rank_stat(tournament_stat, player["rank"])
            final_rank_stat["n_tournaments"] += 1
        else:
            result["n_dual_match"] += 1
            subgame = subgames[0]
            winner = subgame["winner"]
            winner_id = subgame["player_a"] if winner == "A" else subgame["player_b"]
            if winner_id == player_id:
                result["n_dual_wins"] += 1
            else:
                result["n_dual_looses"] += 1

    return result


class HistoryViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    logger = logging.getLogger("HistoryViewSet")
    queryset = Game.objects.all()
    lookup_field = "user__intra_id"
    lookup_url_kwarg = "intra_id"
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        try:
            user = User.objects.get(intra_id=kwargs["intra_id"])
            self.logger.debug(f"got User: {user}")

            result = get_subgame_history_of_user(user)
            self.logger.debug(f"result {result}")
            return Response(data=result, status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)


class StatsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    logger = logging.getLogger("StatsViewSet")
    queryset = Game.objects.all()
    lookup_field = "user__intra_id"
    lookup_url_kwarg = "intra_id"
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        try:
            user = User.objects.get(intra_id=kwargs["intra_id"])
            self.logger.debug(f"got User: {user}")

            result = get_subgame_history_of_user(user)
            self.logger.debug(f"result {result}")

            stats = subgame_history_to_stats(result)
            self.logger.debug(f"stats {stats}")

            return Response(data=stats, status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)

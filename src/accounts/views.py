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
from accounts.GameHistory import get_game_histories_of_user
from accounts.GameStats import GameStats


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


class HistoryViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    logger = logging.getLogger("HistoryViewSet")
    lookup_field = "user__intra_id"
    lookup_url_kwarg = "intra_id"
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Override to satisfy DRF requirements, but not used for custom actions.
        pass

    def get_serializer_class(self):
        # Override to satisfy DRF requirements, but not used for custom actions.
        pass

    def retrieve(self, request, *args, **kwargs):
        try:
            user = User.objects.get(intra_id=kwargs["intra_id"])
            self.logger.debug(f"got User: {user}")

            histories = get_game_histories_of_user(user)
            self.logger.debug(f"result {histories}")

            dict_histories = [history.to_dict() for history in histories]
            return Response(data=dict_histories, status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)


class StatsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    logger = logging.getLogger("StatsViewSet")
    queryset = Game.objects.all()
    lookup_field = "user__intra_id"
    lookup_url_kwarg = "intra_id"
    serializer_class = GameSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        try:
            user = User.objects.get(intra_id=kwargs["intra_id"])
            self.logger.debug(f"got User: {user}")

            histories = get_game_histories_of_user(user)
            self.logger.debug(f"result {histories}")

            stats = GameStats(histories)
            self.logger.debug(f"stats {stats}")

            return Response(data=stats.to_dict(), status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)

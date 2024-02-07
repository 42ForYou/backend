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
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, JSONParser
import json
import pong.settings as settings


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
            instance = self.get_object()
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
                response_data["friend_status"] = friend_status
            else:
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
            raise Response(e.detail, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)

    def save_image(self, image_obj, intra_id, profile):
        extension = self.get_extension(image_obj.content_type)
        if not extension:
            raise CustomError(
                exception="Invalid image type",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        hashed_filename = hashlib.sha256(intra_id.encode()).hexdigest() + extension
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, settings.AVATAR_LOCATION, hashed_filename)

        if profile.avatar and profile.avatar != "default.jpg":
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

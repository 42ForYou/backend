from rest_framework import mixins, viewsets
from .models import Profile
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
from drf_yasg.utils import swagger_auto_schema
from pong.utils import CookieTokenAuthentication, CustomError
import hashlib
import os
import shutil
from django.core.files.storage import default_storage


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user.intra_id == request.user.intra_id


class ProfileViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
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
            else:
                serializer = ProfileSerializer(instance)
            return Response(
                DataWrapperSerializer(
                    {"user": serializer.data, "match_history": [{}]},
                    inner_serializer=ProfileResponseSerializer,
                ).data,
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
            if request.content_type.startswith("image/"):
                profile = request.user.profile
                image_path = self.save_image(request, request.user.intra_id, profile)
                profile.avator = image_path
                profile.save()
            else:
                if "data" not in request.data:
                    raise CustomError(
                        exception="Invalid request",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                data = request.data.get("data")
                instance = self.get_object()
                serializer = self.get_serializer(instance, data=data, partial=True)
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
        except Exception as e:
            raise CustomError(e, "Profile", status_code=status.HTTP_400_BAD_REQUEST)

    def save_image(self, request, intra_id, profile):
        hased_filename = hashlib.sha256(intra_id.encode()).hexdigest()
        file_path = f"images/avator/{hased_filename}.jpeg"

        with open(file_path, "wb") as image_file:
            image_file.write(request.data)

        if profile.avator and profile.avator != "default.jpg":
            pre_file_path = os.join("images/avator/", profile.avator)
            if default_storage.exists(pre_file_path):
                default_storage.delete(pre_file_path)

        return file_path

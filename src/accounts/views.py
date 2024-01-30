from rest_framework import mixins, viewsets
from .models import Profile
from .serializers import (
    ProfileSerializer,
    ProfileNotOwnerSerializer,
    ProfileResponseSerializer,
    DataWrapperSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from pong.utils import custom_exception_handler, CustomError, wrap_data


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
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if request.user.intra_id != kwargs["intra_id"]:
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
            raise e

    def update(self, request, *args, **kwargs):
        if "data" in request.data:
            request.data = request.data["data"]
        return super().update(request, *args, **kwargs)

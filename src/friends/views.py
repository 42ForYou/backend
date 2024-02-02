from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Friend
from .serializers import *

from pong.utils import CustomError, CookieTokenAuthentication, wrap_data
from django.db.models import Q
from game.views import CustomPageNumberPagination


class FriendViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
):
    queryset = Friend.objects.all()
    serializer_class = FriendSerializer
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    # 친구 신청
    def create(self, request, *args, **kwargs):
        try:
            data = request.data.get("data")
            if request.user.intra_id != data.get("requester"):
                raise CustomError("Invalid requester", status.HTTP_400_BAD_REQUEST)
            recevier = Profile.objects.get(intra_id=data.get("receiver")).user
            data["receiver"] = recevier.intra_id
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response(
                wrap_data(friend=serializer.data), status=status.HTTP_201_CREATED
            )
        except Exception as e:
            raise CustomError(e, status.HTTP_400_BAD_REQUEST)

    # 친구 목록
    def list(self, request, *args, **kwargs):
        try:
            paginator = CustomPageNumberPagination()
            user = request.user
            status = request.query_params.get("filter", None)
            if status in ["pending", "friend"]:
                queryset = self.get_queryset().filter(
                    Q(requester=request.user) | Q(receiver=request.user), status=status
                )
            else:
                raise CustomError("Invalid filter", status.HTTP_400_BAD_REQUEST)
            context = paginator.paginate_queryset(queryset, request)
            return paginator.get_paginated_response(context)
        except Exception as e:
            raise CustomError(e, "Friend", status.HTTP_400_BAD_REQUEST)

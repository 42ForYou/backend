from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.views import View
from django.contrib.auth import login, logout
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from accounts.models import User, Profile
from accounts.serializers import UserSerializer, ProfileSerializer

from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import IntegrityError

import json


async def create_profile(request, user):
    # creste profile if not exists
    profile, _ = await sync_to_async(Profile.objects.get_or_create)(
        user=user,
        nickname=user.intra_id,
        email=user.intra_id + "@42seoul.kr",
        image="default.jpg",
    )


async def load_json_data(request):
    try:
        return json.loads(request.body), None
    except json.decoder.JSONDecodeError:
        return None, JsonResponse(
            {"status": False, "error": "Invalid JSON"}, status=400
        )


@database_sync_to_async
def authenticate_user_and_token(intra_id, request):
    try:
        token_key = (
            request.META.get("HTTP_AUTHORIZATION", "").split()[1]
            if "HTTP_AUTHORIZATION" in request.META
            else None
        )
        user = User.objects.get(intra_id=intra_id)
        token = Token.objects.get(user=user, key=token_key)
        if token:
            return user, None  # 유효한 토큰인 경우
        else:
            return None, JsonResponse(
                {"status": False, "error": "Invalid Token"}, status=401
            )
    except (User.DoesNotExist, Token.DoesNotExist):
        return (
            None,
            JsonResponse({"status": False, "error": "Invalid Token"}, status=401),
        )


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(View):
    async def post(self, request, *args, **kwargs):
        data, error = await load_json_data(request)
        if error:
            return error
        serializer = UserSerializer(data=data)
        if await sync_to_async(serializer.is_valid)():
            user = await self.create_user(serializer.validated_data)
            if user:
                await create_profile(request, user)
                user_dict = await sync_to_async(model_to_dict)(user)
                user_dict.pop("password", None)
                return JsonResponse({"status": True, "data": user_dict}, status=201)
            else:
                return JsonResponse({"status": False}, status=400)
        return JsonResponse(serializer.errors, status=400)

    @database_sync_to_async
    def create_user(self, validated_data):
        try:
            validated_data["username"] = validated_data["intra_id"]
            user = User.objects.create_user(**validated_data)
            return user
        except IntegrityError as e:
            return None

    async def get(self, request, *args, **kwargs):
        users = await self.get_users()
        return JsonResponse({"status": True, "data": users}, status=200)

    @database_sync_to_async
    def get_users(self):
        return list(User.objects.all().values("intra_id", "email"))

    async def delete(self, request, *args, **kwargs):
        data, error = await load_json_data(request)
        if error:
            return error
        intra_id = data.get("intra_id")
        user, error = await authenticate_user_and_token(intra_id, request)
        if error:
            return error
        success = await self.delete_user(user)
        if success:
            return JsonResponse({"status": True}, status=200)
        else:
            return JsonResponse({"status": False}, status=400)

    @database_sync_to_async
    def delete_user(self, user):
        if user:
            user.delete()
            return True
        return False


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    async def post(self, request, *args, **kwargs):
        data, error = await load_json_data(request)
        if error:
            return error
        user = await self.authenticate_user(data["intra_id"], data["password"])
        if user:
            await self.login_user(request, user)
            token, _ = await sync_to_async(Token.objects.get_or_create)(user=user)
            return JsonResponse(
                {"status": True, "data": {"token": str(token)}}, status=200
            )
        else:
            return JsonResponse({"status": False}, status=400)

    @database_sync_to_async
    def authenticate_user(self, intra_id, password):
        try:
            user = User.objects.get(intra_id=intra_id)
            user = authenticate(username=user.username, password=password)
            if user:
                return user
            return None
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def login_user(self, request, user):
        login(request, user)

    async def get(self, request, *args, **kwargs):
        data, error = await load_json_data(request)
        if error:
            return error
        user = await self.get_user(data.get("intra_id"), request)
        if user:
            user_dict = await sync_to_async(model_to_dict)(user)
            user_dict.pop("password", None)
            return JsonResponse({"status": True, "data": user_dict}, status=200)
        else:
            return JsonResponse({"status": False}, status=401)

    @database_sync_to_async
    def get_user(self, intra_id, request):
        try:
            user = User.objects.get(intra_id=intra_id)
            logged_in_user_id = request.session.get("_auth_user_id")
            return user if str(user.intra_id) == logged_in_user_id else None
        except User.DoesNotExist:
            return None


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(View):
    async def post(self, request, *args, **kwargs):
        data, error = await load_json_data(request)
        if error:
            return error
        user, error = await authenticate_user_and_token(data["intra_id"], request)
        if error:
            return error
        logged_out = await self.logout_user(user, request)
        if logged_out:
            return JsonResponse({"status": True}, status=200)
        return JsonResponse({"status": False, "error": "user not found"}, status=401)

    @database_sync_to_async
    def logout_user(self, user, request):
        try:
            if user == request.user:
                logout(request)
                return True
            return False
        except User.DoesNotExist:
            return False


from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from asgiref.sync import sync_to_async
from rest_framework.response import Response


class ProfileViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

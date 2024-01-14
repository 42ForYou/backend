from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.views import View
from django.contrib.auth import login, logout
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

from accounts.models import User
from accounts.serializers import UserSerializer

from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import IntegrityError

import json


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(View):
    async def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=json.loads(request.body))

        if await sync_to_async(serializer.is_valid)():
            user = await self.create_user(serializer.validated_data)
            if user:
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
        users_dict = await sync_to_async(model_to_dict)(users)
        return JsonResponse({"status": True, "data": users_dict}, status=200)

    @database_sync_to_async
    def get_users(self):
        users = User.objects.all()
        return [user.intra_id for user in users]

    async def delete(self, request, *args, **kwargs):
        intra_id = json.loads(request.body)["intra_id"]
        success = await self.delete_user(intra_id)
        if success:
            return JsonResponse({"status": True}, status=200)
        else:
            return JsonResponse({"status": False}, status=400)

    @database_sync_to_async
    def delete_user(self, intra_id):
        try:
            user = User.objects.get(intra_id=intra_id)
            user.delete()
            return True
        except User.DoesNotExist:
            return False


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    async def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
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
        user = await self.get_user(request)
        user_dict = await sync_to_async(model_to_dict)(user)
        user_dict.pop("password", None)
        if user:
            return JsonResponse({"status": True, "data": user_dict}, status=200)
        else:
            return JsonResponse({"status": False}, status=400)

    @database_sync_to_async
    def get_user(self, request):
        if request.user.is_authenticated:
            return request.user
        return None

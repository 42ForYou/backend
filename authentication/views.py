from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views import View
from accounts.models import User
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from accounts.serializers import UserSerializer


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(View):
    async def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=json.loads(request.body))

        if await sync_to_async(serializer.is_valid)():
            user = await self.create_user(serializer.validated_data)
            if user:
                return JsonResponse({"intra_id": user.intra_id}, status=201)
            else:
                return JsonResponse({"error": "Unable to signup user."}, status=400)
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
        return JsonResponse({"users": users}, status=200)

    @database_sync_to_async
    def get_users(self):
        users = User.objects.all()
        return [user.intra_id for user in users]

    async def delete(self, request, *args, **kwargs):
        intra_id = json.loads(request.body)["intra_id"]
        success = await self.delete_user(intra_id)
        if success:
            return JsonResponse({"intra_id": intra_id}, status=200)
        else:
            return JsonResponse({"error": "Unable to delete user."}, status=400)

    @database_sync_to_async
    def delete_user(self, intra_id):
        try:
            user = User.objects.get(intra_id=intra_id)
            user.delete()
            return True
        except User.DoesNotExist:
            return False

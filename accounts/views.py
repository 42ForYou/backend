from django.http import JsonResponse
from django.views import View
from .models import User
from django.contrib.auth.hashers import make_password
from channels.db import database_sync_to_async
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import IntegrityError


@method_decorator(csrf_exempt, name="dispatch")
class AsyncRegisterView(View):
    async def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        user = await self.create_user(data)

        if user:
            return JsonResponse({"intra_id": user.intra_id}, status=201)
        else:
            return JsonResponse({"error": "Unable to register user."}, status=400)

    @database_sync_to_async
    def create_user(self, data):
        try:
            user = User.objects.create(
                intra_id=data["intra_id"],
                password=make_password(data["password"]),
            )
            return user
        except IntegrityError as e:
            return None

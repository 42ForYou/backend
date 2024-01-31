from django.shortcuts import redirect
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout
from urllib.parse import quote
from pong.utils import (
    custom_exception_handler,
    CustomError,
    wrap_data,
    CookieTokenAuthentication,
)
from accounts.serializers import UserSerializer, ProfileSerializer


class LoginView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("http://localhost:8000/oauth/")
        redirect_url = quote(settings.CALLBACK_URL)
        url = f"{settings.OAUTH_URL}?client_id={settings.CLIENT_ID}&redirect_uri={redirect_url}&response_type=code"
        return Response(wrap_data(url=url), status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
            logout(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Token.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# Token 유효성 검증 view
class TokenValidationView(APIView):
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user = UserSerializer(request.user).data
        profile = ProfileSerializer(request.user.profile).data
        return Response(
            wrap_data(user=user, profile=profile), status=status.HTTP_200_OK
        )

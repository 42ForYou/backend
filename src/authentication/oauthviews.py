import requests
import json
import requests
import json
from django.contrib.auth import login
from django.conf import settings
from django.forms import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from accounts.models import User, Profile
from accounts.serializers import (
    UserSerializer,
    ProfileSerializer,
)
from pong.utils import custom_exception_handler, CustomError, wrap_data, send_email
from .models import OAuth, TwoFactorAuth
from pong.utils import CookieTokenAuthentication


class OAuthView(APIView):
    def joinUserData(self, user):
        profile = Profile.objects.get(user=user)
        userJson = UserSerializer(user).data
        profileJson = ProfileSerializer(profile).data
        return wrap_data(user=userJson, profile=profileJson)

    def get(self, request):
        try:
            user, token = CookieTokenAuthentication().authenticate(request)
            response = Response(self.joinUserData(user), status=status.HTTP_200_OK)
            response.set_cookie(
                "pong_token", token.key, httponly=True
            )  # remove samesite=strict for development
            return response
        except Exception as e:
            pass

        try:
            code = request.GET.get("code")
            response = self.request42OAuth(code)
            userData = self.request42UserData(response.json()["access_token"])
            user, profile = self.createUserProfileOauth(userData, response)
            if profile.two_factor_auth:
                self.do_2fa(user)
                data = wrap_data(email=profile.email, intra_id=user.intra_id)
                return Response(data=data, status=status.HTTP_428_PRECONDITION_REQUIRED)
            token, created = Token.objects.get_or_create(user=user)
            if created:
                token.save()
            response = Response(self.joinUserData(user), status=status.HTTP_200_OK)
            response.set_cookie(
                "pong_token", token.key, httponly=True
            )  # remove samesite=strict for development
            return response
        except Exception as e:
            raise CustomError(e)

    def do_2fa(self, user):
        two_factor_auth, created = TwoFactorAuth.objects.get_or_create(user=user)
        two_factor_auth.send_secret_code()

    def request42OAuth(self, code):
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.CALLBACK_URL,
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            settings.TOKEN_URL,
            data=json.dumps(data),
            headers=headers,
        )
        if response.status_code != 200:
            raise CustomError(response.text, status_code=response.status_code)
        return response

    def request42UserData(self, access_token):
        userData = requests.get(
            "https://api.intra.42.fr/v2/me",
            headers={"Authorization": "Bearer " + access_token},
        )
        if userData.status_code != 200:
            raise CustomError(userData.text, status_code=userData.status_code)
        return userData

    def createUserProfileOauth(self, userData, response):
        data = {
            "intra_id": userData.json()["login"],
            "username": userData.json()["login"],
            "email": userData.json()["email"],
        }
        try:
            user = User.objects.get(intra_id=data["intra_id"])
            return user, user.profile
        except User.DoesNotExist:
            pass

        try:
            serializer = UserSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            profile = Profile.objects.create(
                user=user,
                nickname=data["intra_id"],
                email=data["email"],
                avatar="",
            )
            oauth = OAuth.objects.create(
                user=user,
                access_token=response.json()["access_token"],
                refresh_token=response.json()["refresh_token"],
                token_type=response.json()["token_type"],
            )
            return user, profile
        except Exception as e:
            if user:
                user.delete()
            if profile:
                profile.delete()
            if oauth:
                oauth.delete()
            raise CustomError(e, status_code=status.HTTP_400_BAD_REQUEST)

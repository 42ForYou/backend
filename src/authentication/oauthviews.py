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
    UserTokenProfileSerializer,
    DataWrapperSerializer,
)
from .models import OAuth
import requests
import json


class OAuthView(APIView):
    def joinUserData(self, user, token):
        profile = Profile.objects.get(user=user)
        userJson = UserSerializer(user).data
        profileJson = ProfileSerializer(profile).data
        return DataWrapperSerializer(
            {"token": token, "user": userJson, "profile": profileJson},
            inner_serializer=UserTokenProfileSerializer,
        ).data

    def get(self, request):
        if request.user.is_authenticated:
            try:
                user = User.objects.get(intra_id=request.user.intra_id)
                token, created = Token.objects.get_or_create(user=user)
                if created:
                    token.save()
                return Response(
                    self.joinUserData(user, token.key), status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                pass
        try:
            code = request.GET.get("code")
            response = self.request42OAuth(code)
            if response.status_code != 200:
                return response
            userData = self.request42UserData(response.json()["access_token"])
            if userData.status_code != 200:
                return userData
            user = self.createUserProfileOauth(userData, response)
            token, created = Token.objects.get_or_create(user=user)
            if created:
                token.save()
            # login(request, user)
            return Response(
                self.joinUserData(user, token.key), status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def request42OAuth(self, code):
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "code": code,
            "redirect_uri": "http://localhost:8000/oauth/",
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            "https://api.intra.42.fr/oauth/token",
            data=json.dumps(data),
            headers=headers,
        )
        response.raise_for_status()
        return response

    def request42UserData(self, access_token):
        userData = requests.get(
            "https://api.intra.42.fr/v2/me",
            headers={"Authorization": "Bearer " + access_token},
        )
        userData.raise_for_status()
        return userData

    def createUserProfileOauth(self, userData, response):
        data = {
            "intra_id": userData.json()["login"],
            "username": userData.json()["login"],
            "email": userData.json()["email"],
        }
        try:
            user = User.objects.get(intra_id=data["intra_id"])
            return user
        except User.DoesNotExist:
            pass

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            profile = Profile.objects.create(
                user=user,
                nickname=data["intra_id"],
                email=data["email"],
                avator="default.jpg",
            )
            profile.save()
            oauth = OAuth.objects.create(
                user=user,
                access_token=response.json()["access_token"],
                refresh_token=response.json()["refresh_token"],
                token_type=response.json()["token_type"],
            )
            oauth.save()
            return user
        else:
            raise ValidationError(serializer.errors)

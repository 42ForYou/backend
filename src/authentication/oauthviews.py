from django.contrib.auth import login
from django.conf import settings
from django.forms import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from accounts.models import User, Profile
from accounts.serializers import UserSerializer, ProfileSerializer
from .models import OAuth
import requests
import json


class OAuthView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                user = User.objects.get(intra_id=request.user.intra_id)
                token, created = Token.objects.get_or_create(user=user)
                if created:
                    token.save()
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                pass

        code = request.GET.get("code")
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        response = request42OAuth(code)
        if response.status_code != 200:
            return response
        userData = request42UserData(response.json()["access_token"])
        if userData.status_code != 200:
            return userData
        user = createUserProfileOauth(userData, response)
        userJson = UserSerializer(user).data
        profile = Profile.objects.get(user=user)
        profileJson = ProfileSerializer(profile).data
        token, created = Token.objects.get_or_create(user=user)
        if created:
            token.save()
        login(request, user)
        return Response(
            {"token": token.key, "user": userJson, "profile": profileJson},
            status=status.HTTP_200_OK,
        )


def request42OAuth(code):
    try:
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
    except requests.exceptions.RequestException as e:
        return Response(
            {"detail": "Error while requesting oauth: " + str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return response


def request42UserData(access_token):
    try:
        userData = requests.get(
            "https://api.intra.42.fr/v2/me",
            headers={"Authorization": "Bearer " + access_token},
        )
        userData.raise_for_status()
    except requests.exceptions.RequestException as e:
        return Response(
            {"detail": "Error while requesting user data: " + str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return userData


def createUserProfileOauth(userData, response):
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
    try:
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            profile = Profile.objects.create(
                user=user,
                nickname=data["intra_id"],
                email=data["email"],
                image="default.jpg",
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
    except ValidationError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        User.objects.delete(intra_id=data["intra_id"])
        return Response(
            {"detail": "Unexpected error occurred: " + str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

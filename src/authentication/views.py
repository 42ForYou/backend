from django.shortcuts import redirect
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout
from urllib.parse import quote


class LoginView(APIView):
    def get(self, request):
        print(request.headers)
        if request.user.is_authenticated:
            return redirect("http://localhost:8000/oauth/")
        redirect_url = quote("http://localhost:8000/oauth/")
        return Response(
            {
                "data": {
                    "url": f"https://api.intra.42.fr/oauth/authorize?client_id={settings.CLIENT_ID}&redirect_uri={redirect_url}&response_type=code"
                }
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
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

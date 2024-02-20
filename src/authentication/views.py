from django.shortcuts import redirect
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout
from django.db.models import Prefetch
from urllib.parse import quote
from pong.utils import CustomError, wrap_data, CookieTokenAuthentication, send_email
from accounts.serializers import UserSerializer, ProfileSerializer


# TODO: Add check token when login
# if request.COOKIES.get("pong_token"):
#     token = request.COOKIES.get("pong_token")
#     try:
#         token = Token.objects.get(key=token)
#         user = token.user
#         user_serializer = UserSerializer(user).data
#         profile_serializer = ProfileSerializer(user.profile).data
#         return Response(
#             wrap_data(user=user_serializer, profile=profile_serializer),
#             status=status.HTTP_200_OK,
#         )
#     except Exception as e:
#         response = Response(status=status.HTTP_400_BAD_REQUEST)
#         response.delete_cookie("pong_token")
#         return response
class LoginView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request):
        # TODO: Add check token when login
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
            response = Response(status=status.HTTP_204_NO_CONTENT)
            response.delete_cookie("pong_token")
            return response
        except Token.DoesNotExist:
            response = Response(status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie("pong_token")
            return Response(status=status.HTTP_400_BAD_REQUEST)


# Token 유효성 검증 view
class TokenValidationView(APIView):
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        if not request.user.is_authenticated:
            response = Response(status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie("pong_token")
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user = UserSerializer(request.user).data
        profile = ProfileSerializer(request.user.profile).data
        user.update(profile)
        return Response(wrap_data(user=user), status=status.HTTP_200_OK)


class TwoFactorAuthView(APIView):
    authentication_classes = ()

    def get(self, request):
        try:
            intra_id = request.query_params.get("intra_id")
            code = request.query_params.get("code")
            user = User.objects.get(intra_id=intra_id)
            two_factor_auth = user.two_factor_auth
            if two_factor_auth.is_valid(code):
                user_serializer = UserSerializer(user).data
                profile_serializer = ProfileSerializer(user.profile).data
                token, created = Token.objects.get_or_create(user=user)
                if created:
                    token.save()
                response = Response(
                    data=wrap_data(user=user_serializer, profile=profile_serializer),
                    status=status.HTTP_200_OK,
                )
                response.set_cookie(
                    "pong_token", token.key, httponly=True
                )  # remove samesite=strict for development
                return response
            else:
                return Response(
                    data={"error": "Invalid Code"}, status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            return CustomError(
                exception=e, model_name="user", status_code=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, *args, **kwargs):
        data = request.data.get("data")
        email = data["email"]
        user = User.objects.get(intra_id=data["intra_id"])
        two_factor_auth = user.two_factor_auth
        new_code = two_factor_auth.generate_secret_key()
        two_factor_auth.secret_code = new_code
        two_factor_auth.save()
        send_email(
            "PlanetPong 2FA Code",
            f"Your Code is {new_code}",
            settings.EMAIL_HOST_USER,
            [email],
        )
        return Response(status=status.HTTP_200_OK)

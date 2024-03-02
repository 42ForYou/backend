from urllib.parse import quote

from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pong.utils import CustomError, wrap_data, CookieTokenAuthentication
from accounts.serializers import UserSerializer, ProfileSerializer
from accounts.models import User


class LoginView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request):
        redirect_url = quote(settings.CALLBACK_URL)
        url = (
            f"{settings.OAUTH_URL}?client_id={settings.CLIENT_ID}"
            f"&redirect_uri={redirect_url}&response_type=code"
        )
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
            intra_id = request.query_params.get("intra-id")
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
                    "pong_token", token.key, httponly=True, samesite=None
                )  # remove samesite=strict for development
                return response
            else:
                return Response(
                    data={"error": "Invalid Code"}, status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            raise CustomError(
                exception=e, model_name="user", status_code=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data.get("data")
            user = User.objects.get(intra_id=data["intra_id"])
            user.two_factor_auth.send_secret_code()
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            raise CustomError(
                exception=e, model_name="user", status_code=status.HTTP_400_BAD_REQUEST
            )

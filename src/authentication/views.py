import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.tokens import RefreshToken
from urllib.parse import quote
from pong.utils import CustomError, wrap_data, CookieTokenAuthentication
import pong.settings as settings
from accounts.serializers import UserSerializer, ProfileSerializer
from accounts.models import User
from .utils import get_token_for_user, set_cookie_response


class LoginView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request):
        redirect_url = quote(settings.CALLBACK_URL)
        url = f"{settings.OAUTH_URL}?client_id={settings.CLIENT_ID}&redirect_uri={redirect_url}&response_type=code"
        return Response(wrap_data(url=url), status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if refresh_token:
                refresh = RefreshToken(refresh_token)
                refresh.blacklist()
        except Exception as e:
            pass
        response.delete_cookie("pong_token")
        response.delete_cookie("refresh_token")

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        logger = logging.getLogger("authentication.TokenRefreshView")
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            raise CustomError("Invalid token", status_code=status.HTTP_401_UNAUTHORIZED)

        request.data["refresh"] = refresh_token
        try:
            response = super().post(request, *args, **kwargs)
            token = response.data["access"]
            response.data = None
            response.set_cookie(
                "pong_token", token, httponly=True, samesite="Strict", path="/"
            )  # remove samesite=strict for development
            logger.debug(f"refreshed token: {token}")
            return response
        except Exception as e:
            raise CustomError("Invalid token", status_code=status.HTTP_401_UNAUTHORIZED)


# JWT 유효성 검사
# 401 토큰 불량
# 403 토큰 없음
class CustomTokenVerifyView(TokenVerifyView):
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        if not request.user.is_authenticated:
            response = Response(status=status.HTTP_401_UNAUTHORIZED)
            return response
        user = UserSerializer(request.user).data
        profile = ProfileSerializer(request.user.profile).data
        user.update(profile)
        return Response(wrap_data(user=user), status=status.HTTP_200_OK)


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
                token = get_token_for_user(user)
                response = Response(
                    data=wrap_data(user=user_serializer, profile=profile_serializer),
                    status=status.HTTP_200_OK,
                )
                response = set_cookie_response(
                    response, token["access"], token["refresh"]
                )
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

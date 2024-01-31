from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token


class CustomError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status
        super().__init__(self.message)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, CustomError):
        return Response({"error": exc.message}, status=exc.status)

    if response is not None:
        response.data["error"] = str(exc)
    return response


def wrap_data(**kwargs):
    return {"data": kwargs}


class CookieTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token_key = request.COOKIES.get("kimyeonhkimbabo_token")
        if not token_key:
            return None

        try:
            token = Token.objects.get(key=token_key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        return (token.user, token)

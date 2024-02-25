from rest_framework_simplejwt.tokens import RefreshToken


def get_token_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def set_cookie_response(response, access=None, refresh=None):
    if access:
        response.set_cookie(
            "pong_token",
            access,
            httponly=True,
            samesite="Strict",
            path="/",
        )
    if refresh:
        response.set_cookie(
            "refresh_token",
            refresh,
            httponly=True,
            samesite="Strict",
            path="/",
        )
    return response

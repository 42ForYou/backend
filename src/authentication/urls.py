from django.urls import path
from .views import LoginView, LogoutView, TokenValidationView, TwoFactorAuthView
from .oauthviews import OAuthView


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("oauth/", OAuthView.as_view(), name="oauth"),
    path("valid/", TokenValidationView.as_view(), name="valid"),
    path("2fa/", TwoFactorAuthView.as_view(), name="2fa"),
]

from django.urls import path, include
from .views import ProfileViewSet, OAuthView, OAuthCodeView, RegisterView
from rest_framework import routers

router = routers.DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profiles")

urlpatterns = [
    path("", include(router.urls), name="profiles"),
    path("oauth/", OAuthView.as_view(), name="oauth"),
    path("oauth/code/", OAuthCodeView.as_view(), name="oauth_code"),
    path("register/", RegisterView.as_view(), name="register"),
]

from django.urls import path, include
from .views import RegisterView, LoginView, LogoutView, ProfileViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profiles")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", include(router.urls), name="profiles"),
]

from django.urls import path, include
from rest_framework import routers

from .views import FriendViewSet

router = routers.DefaultRouter()
router.register("", FriendViewSet, basename="friends")

urlpatterns = [
    path("", include(router.urls)),
]

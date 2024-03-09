from django.urls import path, include
from .views import FriendViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register("", FriendViewSet, basename="friends")

urlpatterns = [
    path("", include(router.urls)),
]

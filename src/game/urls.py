from .views import GameRoomViewSet, PlayerViewSet, SubGameViewSet
from django.urls import re_path, path, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register("game_rooms", GameRoomViewSet, basename="game_rooms")
router.register("players", PlayerViewSet, basename="players")
router.register("subgames", SubGameViewSet, basename="subgames")

urlpatterns = [
    path("", include(router.urls)),
]

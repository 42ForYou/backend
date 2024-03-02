from django.urls import path, include
from rest_framework import routers

from .views import GameRoomViewSet, PlayerViewSet, SubGameViewSet

router = routers.DefaultRouter()
router.register("game_rooms", GameRoomViewSet, basename="game_rooms")
router.register("players", PlayerViewSet, basename="players")
router.register("subgames", SubGameViewSet, basename="subgames")

urlpatterns = [
    path("", include(router.urls)),
]

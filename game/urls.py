from .views import GameRoomViewSet, PlayerViewSet
from django.urls import re_path, path, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register("game_rooms", GameRoomViewSet, basename="game_rooms")
router.register("players", PlayerViewSet, basename="players")

urlpatterns = [
    # re_path(r"^game_rooms(?:/(?P<game_id>\d+))?/$", game_rooms_view, name="game_rooms"),
    # path("players/", players_view, name="players"),
    path("", include(router.urls)),
]

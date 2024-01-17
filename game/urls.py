from .views import game_rooms_view, players_view
from django.urls import re_path, path

urlpatterns = [
    re_path(r"^game_rooms(?:/(?P<game_id>\d+))?/$", game_rooms_view, name="game_rooms"),
    path("players/", players_view, name="players"),
]

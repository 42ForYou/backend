from .views import game_rooms
from django.urls import re_path

urlpatterns = [
    re_path(r"^game_rooms(?:/(?P<room_id>\d+))?/$", game_rooms, name="game_rooms"),
]

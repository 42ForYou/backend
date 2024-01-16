from .models import Game, GameRoom
from rest_framework import serializers


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"


class GameRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRoom
        fields = "__all__"


class GameRoomJoinSerializer(serializers.ModelSerializer):
    game = GameSerializer(source="game_id")

    class Meta:
        model = GameRoom
        fields = [
            "room_title",
            "status",
            "join_players",
            "game",
        ]

from .models import Game, GameRoom, GamePlayer
from accounts.models import User
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
            "id",
            "title",
            "status",
            "join_players",
            "game",
        ]


class GamePlayerSerializer(serializers.ModelSerializer):
    intra_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True,
    )

    class Meta:
        model = GamePlayer
        fields = "__all__"

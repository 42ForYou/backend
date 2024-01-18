from .models import Game, GameRoom, GamePlayer
from accounts.models import User
from rest_framework import serializers


class EmptySerializer(serializers.Serializer):
    pass


class HostSerializer(serializers.Serializer):
    intra_id = serializers.CharField()


class RoomSerializer(serializers.Serializer):
    title = serializers.CharField()


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"


class GameRoomCreateSerializer(serializers.Serializer):
    host = HostSerializer()
    game = GameSerializer()
    room = RoomSerializer()


class GameRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRoom
        fields = [
            "id",
            "title",
            "status",
            "join_players",
            "game_id",
        ]


class GetGameRoomSerializer(serializers.ModelSerializer):
    game = GameSerializer(source="game_id")

    class Meta:
        model = GameRoom
        fields = [
            "game",
            "id",
            "title",
            "status",
            "join_players",
            "game_id",
        ]


class GamePlayerSerializer(serializers.ModelSerializer):
    intra_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=True,
    )

    class Meta:
        model = GamePlayer
        fields = "__all__"

from rest_framework import serializers
from .models import Game, GameRoom, GamePlayer, SubGame, GameResult, GameResultEntry
from accounts.models import User


class RoomSerializer(serializers.Serializer):
    title = serializers.CharField()
    join_players = serializers.IntegerField()


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["game_id", "is_tournament", "game_point", "time_limit", "n_players"]


class GameRoomSerializer(serializers.ModelSerializer):
    game = GameSerializer(source="game_id")

    class Meta:
        model = GameRoom
        fields = ["game", "id", "title", "status", "join_players", "host"]

    def create(self, validated_data):
        game_data = validated_data.pop("game_id")
        room_data = validated_data
        game = Game.objects.create(**game_data)
        intra_id = User.objects.get(intra_id=room_data.pop("host"))
        room = GameRoom.objects.create(**room_data, game_id=game, host=intra_id)
        return room


class GamePlayerSerializer(serializers.ModelSerializer):
    intra_id = serializers.SlugRelatedField(
        slug_field="intra_id", queryset=User.objects.all()
    )
    game_id = serializers.SlugRelatedField(
        slug_field="game_id", queryset=Game.objects.all()
    )

    class Meta:
        model = GamePlayer
        fields = ["id", "intra_id", "game_id", "nick_name", "rank"]


class SubGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGame
        fields = "__all__"


class GameResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameResult
        fields = "__all__"


class GameResultEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GameResultEntry
        fields = "__all__"

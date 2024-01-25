from rest_framework import serializers
from .models import Game, GameRoom, GamePlayer, SubGame
from accounts.models import User, Profile
from accounts.serializers import UserSerializer, ProfileNotOwnerSerializer


# Game related serializers
class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["game_id", "is_tournament", "game_point", "time_limit", "n_players"]


class GameRoomSerializer(serializers.ModelSerializer):
    host = serializers.SerializerMethodField()

    class Meta:
        model = GameRoom
        fields = "__all__"

    def get_host(self, obj):
        profile = Profile.objects.get(user=obj.host)
        return profile.nickname

    def create(self, validated_data):
        validated_data.pop("join_players", None)
        validated_data.pop("status", None)
        return super().create(validated_data)


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


## Swagger를 위한 Serializers


class RoomHostSerializer(serializers.Serializer):
    nickname = serializers.CharField()


class RoomSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    join_players = serializers.IntegerField()
    host = RoomHostSerializer()


# Page related serializers
class SwaggerPagesSerializer(serializers.Serializer):
    total_pages = serializers.IntegerField()
    count = serializers.IntegerField()
    current_page = serializers.IntegerField()
    previous_page = serializers.CharField()
    next_page = serializers.CharField()


# Wrapping serializers
class SwaggerGameRoomSerizlizer(serializers.Serializer):
    gmae = GameSerializer()
    room = RoomSerializer()


class SwaggerGameListSerializer(serializers.Serializer):
    data = SwaggerGameRoomSerizlizer(many=True)
    pages = SwaggerPagesSerializer()


class SwaggerGameRetriveSerializer(serializers.Serializer):
    data = SwaggerGameRoomSerizlizer()

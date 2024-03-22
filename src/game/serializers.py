from rest_framework import serializers
from .models import Game, GameRoom, GamePlayer, SubGame
from accounts.models import User, Profile


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["game_id", "is_tournament", "game_point", "time_limit", "n_players"]


class GameRoomSerializer(serializers.ModelSerializer):
    host = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    host_nickname = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GameRoom
        fields = "__all__"
        extra_kwargs = {
            "host": {"write_only": True},
        }

    def get_host_nickname(self, obj):
        profile = Profile.objects.get(user=obj.host)
        return profile.nickname

    def create(self, validated_data):
        host_user = validated_data.pop("host", None)
        validated_data["host"] = host_user
        game_room = GameRoom.objects.create(**validated_data)
        return game_room

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["host"] = self.get_host_nickname(instance)
        representation.pop("host_nickname", None)

        return representation


class GamePlayerSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GamePlayer
        fields = ["id", "user", "avatar", "game", "nickname", "rank"]
        extra_kwargs = {
            "user": {"write_only": True},
        }

    def get_avatar(self, obj):
        return obj.user.profile.avatar

    def create(self, validated_data):
        user = User.objects.get(intra_id=validated_data["user"])
        validated_data["nickname"] = user.profile.nickname
        return super().create(validated_data)


class SubGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGame
        fields = "__all__"

from .models import Game, GameRoom, GamePlayer
from accounts.models import User
from rest_framework import serializers


# class EmptySerializer(serializers.Serializer):
#     pass


# class HostSerializer(serializers.Serializer):
#     intra_id = serializers.CharField()


# class RoomSerializer(serializers.Serializer):
#     class Meta:
#         model = GameRoom
#         fields = "__all__"


# class GameSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Game
#         fields = "__all__"


# class GameRoomCreateSerializer(serializers.Serializer):
#     host = HostSerializer()
#     game = GameSerializer()
#     room = RoomSerializer()


# class GameRoomSerializer(serializers.ModelSerializer):
#     host = HostSerializer()
#     game = GameSerializer()
#     room = RoomSerializer()

#     class Meta:
#         model = GameRoom
#         fields = [
#             "host",
#             "game",
#             "room",
#         ]


# class GetGameRoomSerializer(serializers.ModelSerializer):
#     game = GameSerializer(source="game_id")

#     class Meta:
#         model = GameRoom
#         fields = [
#             "game",
#             "id",
#             "title",
#             "status",
#             "join_players",
#             "game_id",
#         ]


# class GamePlayerSerializer(serializers.ModelSerializer):
#     intra_id = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.all(),
#         required=True,
#     )

#     class Meta:
#         model = GamePlayer
#         fields = "__all__"


from rest_framework import serializers
from .models import Game, GameRoom, GamePlayer
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

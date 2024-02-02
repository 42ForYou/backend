from rest_framework import serializers
from .models import Friend
from accounts.models import User, Profile
from accounts.serializers import ProfileSerializer


class FriendUserSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source="profile.nickname")
    avatar = serializers.ImageField(source="profile.avatar")

    class Meta:
        model = User
        fields = ["nickname", "avatar"]


class FriendSerializer(serializers.ModelSerializer):
    requester = FriendUserSerializer(source="requester", read_only=True)
    receiver = FriendUserSerializer(source="receiver", read_only=True)

    class Meta:
        model = Friend
        fields = ["id", "requester", "receiver", "status", "created_at"]

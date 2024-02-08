from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework import status
from pong.utils import CustomError

from .models import User, Profile


class UserTokenProfileSerializer(serializers.Serializer):
    user = serializers.JSONField()
    profile = serializers.JSONField()


class ProfileResponseSerializer(serializers.Serializer):
    user = serializers.JSONField()
    match_history = serializers.JSONField()


class DataWrapperSerializer(serializers.Serializer):
    data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.inner_serializer = kwargs.pop("inner_serializer", None)
        super().__init__(*args, **kwargs)

    def get_data(self, obj):
        return self.inner_serializer(obj).data


class UserSerializer(serializers.ModelSerializer):
    intra_id = serializers.CharField(
        max_length=32, validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ("intra_id",)

    def create(self, validated_data):
        validated_data["username"] = validated_data["intra_id"]
        user = User.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    intra_id = serializers.CharField(source="user.intra_id", read_only=True)

    class Meta:
        model = Profile
        fields = ("intra_id", "nickname", "email", "avatar", "two_factor_auth")

    def validate(self, data):
        errors = {}
        if "nickname" in data:
            nickname = data.get("nickname")
            if not (self.instance and self.instance.nickname == nickname):
                if Profile.objects.filter(nickname=data["nickname"]).exists():
                    errors["nickname"] = ["This nickname is already taken."]
        if "email" in data:
            email = data.get("email")
            if not (self.instance and self.instance.email == email):
                if Profile.objects.filter(email=data["email"]).exists():
                    errors["email"] = ["This email is already taken."]
        if errors:
            raise serializers.ValidationError(errors)
        return data


class ProfileNotOwnerSerializer(serializers.ModelSerializer):
    intra_id = serializers.CharField(source="user.intra_id", read_only=True)

    class Meta:
        model = Profile
        fields = ("intra_id", "nickname", "avatar")


class SwaggerProfileSerializer(serializers.Serializer):
    user = ProfileSerializer()
    match_history = serializers.JSONField()


class WrapDataSwaggerProfileSerializer(serializers.Serializer):
    data = SwaggerProfileSerializer()


class OnlyUserProfileSerializer(serializers.Serializer):
    user = ProfileSerializer()


class WrapDataSwaggerOnlyProfileSerializer(serializers.Serializer):
    data = OnlyUserProfileSerializer()

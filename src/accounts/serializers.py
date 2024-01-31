from rest_framework import serializers
from rest_framework.validators import UniqueValidator

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
        fields = ("intra_id", "nickname", "email", "avator", "two_factor_auth")
        extra_kwargs = {
            "nickname": {
                "validators": [UniqueValidator(queryset=Profile.objects.all())],
                "required": False,
            },
            "email": {
                "validators": [UniqueValidator(queryset=Profile.objects.all())],
                "required": False,
            },
        }


class ProfileNotOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("nickname", "avator")


class SwaggerProfileSerializer(serializers.Serializer):
    user = ProfileSerializer()
    match_history = serializers.JSONField()


class WrapDataSwaggerProfileSerializer(serializers.Serializer):
    data = SwaggerProfileSerializer()


class OnlyUserProfileSerializer(serializers.Serializer):
    user = ProfileSerializer()


class WrapDataSwaggerOnlyProfileSerializer(serializers.Serializer):
    data = OnlyUserProfileSerializer()

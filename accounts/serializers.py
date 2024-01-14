from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

from .models import User


class UserSerializer(serializers.ModelSerializer):
    intra_id = serializers.CharField(
        max_length=32, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = (
            "intra_id",
            "password",
        )

    def create(self, validated_data):
        validated_data["username"] = validated_data["intra_id"]
        user = User.objects.create_user(**validated_data)
        return user

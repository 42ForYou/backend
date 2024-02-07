from rest_framework import serializers
from .models import Friend
from accounts.models import User, Profile
from accounts.serializers import ProfileSerializer


class FriendUserSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source="profile.nickname")
    avatar = serializers.CharField(source="profile.avatar")

    class Meta:
        model = User
        fields = ["intra_id", "nickname", "avatar"]


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friend
        fields = ["id", "requester", "receiver", "status", "created_at"]

    def to_representation(self, instance):
        # 기본 serialization 결과를 가져옵니다.
        ret = super().to_representation(instance)

        # context에서 request를 가져옵니다.
        request = self.context.get("request")

        # 현재 요청 사용자가 requester인지 receiver인지 확인합니다.
        if request and hasattr(request, "user"):
            current_user = request.user
            if current_user == instance.requester:
                me = FriendUserSerializer(instance.requester).data
                friend = FriendUserSerializer(instance.receiver).data
            else:
                me = FriendUserSerializer(instance.receiver).data
                friend = FriendUserSerializer(instance.requester).data

            # 결과 데이터를 "me"와 "friend"로 구성합니다.
            ret["me"] = me
            ret["friend"] = friend

            # 원래의 requester와 receiver 필드는 제거합니다.
            ret.pop("requester", None)
            ret.pop("receiver", None)

        return ret

import socketio
import logging

from asgiref.sync import sync_to_async
from django.db.models import Q
from rest_framework_simplejwt.tokens import AccessToken
from .models import SocketSession
from friends.serializers import FriendUserSerializer
from friends.models import Friend
from accounts.models import User
import pong.settings as settings


"""
connect, disconnect 에 액세스할 수 없음 에러는 문제없다.
이벤트를 등록하면 자동으로 connect, disconnect 가 등록된다.
connect, disconnect 는 socketio 라이브러리에서 자동으로 등록된다.
"""

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS,
    logger=logging.getLogger("socketio.server"),
    engineio_logger=logging.getLogger("socketio.engineio"),
)

logger = logging.getLogger(f"{__package__}.{__name__}")


@sync_to_async
def get_friends(user):
    friends_queryset = Friend.objects.filter(
        Q(requester=user) | Q(receiver=user),
        status="friend",
    )
    friends_users = set()
    for friend in (list)(friends_queryset):
        if friend.requester == user:
            friends_users.add(friend.receiver)
        else:
            friends_users.add(friend.requester)
    return friends_users


@sync_to_async
def filter_online_friends(friends_users):
    online_friends_sids = set()
    for friend in friends_users:
        if friend.is_online:
            online_friends_sids.add(friend.socket_session.online_session_id)
    return online_friends_sids


@sync_to_async
def get_user_by_token(token):
    validated_token = AccessToken(token)
    intra_id = validated_token["intra_id"]
    user = User.objects.get(intra_id=intra_id)
    return user


@sync_to_async
def get_user_by_sid(sid):
    return (
        SocketSession.objects.filter(
            Q(session_id=sid) | Q(online_session_id=sid) | Q(game_room_session_id=sid)
        )
        .first()
        .user
    )


@sync_to_async
def get_session(user, sid):
    session, created = SocketSession.objects.update_or_create(
        user=user, defaults={"session_id": sid}
    )
    return session


@sync_to_async
def async_frienduserserializer(user):
    return FriendUserSerializer(user).data


@sio.on("connect")
async def connect(sid: str, environ: dict) -> None:
    try:
        cookies = environ.get("HTTP_COOKIE", "")
        cookie_dict = dict(
            item.split("=") for item in cookies.split("; ") if "=" in item
        )
        token = cookie_dict.get(settings.SIMPLE_JWT["AUTH_COOKIE"], None)
        if token:
            user = await get_user_by_token(token)
            session = await get_session(user, sid)
            user.is_online = True
            await sync_to_async(user.save)()
            friends_users = await get_friends(user)
            online_friends_sids = await filter_online_friends(friends_users)
            user_info = await async_frienduserserializer(user)
            user_info.update({"is_online": user.is_online})
            for online_friend_sid in online_friends_sids:
                user = await get_user_by_sid(online_friend_sid)
                # SIO: emit update_friends
                await sio.emit(
                    "update_friends",
                    {"friend": user_info},
                    room=online_friend_sid,
                    namespace="/online_status",
                )
        else:
            await sio.disconnect(sid)
    except Exception as e:
        logger.error(f"Error in connect: {e}")
        await sio.disconnect(sid)


# SIO: F>B disconnect
@sio.on("disconnect")
async def disconnect(sid):
    try:
        user = await get_user_by_sid(sid)
        user.is_online = False
        await sync_to_async(user.save)()
        friends_users = await get_friends(user)
        online_friends_sids = await filter_online_friends(friends_users)
        user_info = await async_frienduserserializer(user)
        user_info.update({"is_online": user.is_online})
        for online_friend_sid in online_friends_sids:
            user = await get_user_by_sid(online_friend_sid)
            # SIO: B>F update_friends
            await sio.emit(
                "update_friends",
                {"friend": user_info},
                room=online_friend_sid,
                namespace="/online_status",
            )
    except Exception as e:
        logger.error(f"Error in disconnect: {e}")

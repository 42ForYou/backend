import socketio
from asgiref.sync import sync_to_async
from django.db.models import Q
from rest_framework.authtoken.models import Token
from pong.utils import wrap_data
from .models import SocketSession
from friends.serializers import FriendUserSerializer
from friends.models import Friend


"""
connect, disconnect 에 액세스할 수 없음 에러는 문제없다.
이벤트를 등록하면 자동으로 connect, disconnect 가 등록된다.
connect, disconnect 는 socketio 라이브러리에서 자동으로 등록된다.
"""

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["https://localhost", "https://localhost:8000"],
    logger=True,
    engineio_logger=True,
)


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
            online_friends_sids.add(friend.socket_session.session_id)
    return online_friends_sids


@sync_to_async
def get_user_by_token(token):
    return Token.objects.get(key=token).user


@sync_to_async
def get_user_by_sid(sid):
    return SocketSession.objects.get(session_id=sid).user


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
        token = cookie_dict.get("kimyeonhkimbabo_token", None)
        if token:
            user = await get_user_by_token(token)
            session = await get_session(user, sid)
            user.is_online = True
            await sync_to_async(user.save)()
            friends_users = await get_friends(user)
            online_friends_sids = await filter_online_friends(friends_users)
            user_info = await async_frienduserserializer(user)
            user_info.update({"is_online": user.is_online})
            # for online_friend_sid in online_friends_sids:
            await sio.emit(
                "update_friends",
                {"friend": user_info},
                namespace="/online_status",
            )
            print("##############Client connected##############", sid)
        else:
            print(f"@@@@@@@@@@@@@@Token not found: {sid}@@@@@@@@@@@@@@@@@@@@@@@@")
            await sio.disconnect(sid)
    except Exception as e:
        print(f"@@@@@@@@@@@@@@Error in connect: {e}@@@@@@@@@@@@@@@@@@@@@@@@")
        await sio.disconnect(sid)


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
        # for online_friend_sid in online_friends_sids:
        await sio.emit(
            "update_friends",
            {"friend": user_info},
            namespace="/online_status",
        )
        print("################Client disconnected############", sid)
    except Exception as e:
        print(f"@@@@@@@@@@@@@@Error in disconnect: {e}@@@@@@@@@@@@@@@@@@@@@@@@")

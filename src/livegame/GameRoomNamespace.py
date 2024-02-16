import asyncio
import socketio
from .databaseio import left_game_room, game_start, update_or_create_matchs_list
from socketcontrol.events import sio
from socketcontrol.events import get_user_by_token
from asgiref.sync import sync_to_async


async def emit_update_room(data, game_room_id, player_id_list, sid_list):
    # for sid in sid_list:
    #     copy_data = data.copy()
    #     copy_data["my_player_id"] = player_id_list[sid_list.index(sid)]
    #     print(f"emit_update_room: {copy_data}")
    #     print(f"emit_update_room: {sid}")
    print(f"namespace: /game/room/{game_room_id}")
    await sio.emit("update_room", data, namespace=f"/game/room/{game_room_id}")


async def emit_destroyed(data, game_room_id):
    await sio.emit("destroyed", data, namespace=f"/game/room/{game_room_id}")


async def emit_update_tournament(data, game_room_id):
    await sio.emit("update_tournament", data, namespace=f"/game/room/{game_room_id}")


@sync_to_async
def update_game_room_sid(user, sid):
    user.socket_session.game_room_session_sid = sid
    print(f"game room namespace ##{user.socket_session.game_room_session_sid}##")
    user.socket_session.save()


class GameRoomNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace, game_room_id):
        super().__init__(namespace=namespace)
        self.game_room_id = game_room_id
        self.match_dict = {}
        print(f"game room namespace ##{self.game_room_id}## created")

    async def on_connect(self, sid, environ):
        try:
            cookies = environ.get("HTTP_COOKIE", "")
            cookie_dict = dict(
                item.split("=") for item in cookies.split("; ") if "=" in item
            )
            token = cookie_dict.get("kimyeonhkimbabo_token", None)
            if token:
                user = await get_user_by_token(token)
                await update_game_room_sid(user, sid)
                user = await get_user_by_token(token)
            else:
                print("No token")
                await self.disconnect(sid)
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.disconnect(sid)

    async def on_exited(self, sid, data):
        # self.emit("my_response", data)
        player_id = data["my_player_id"]
        data, player_id_list, sid_list = await left_game_room(
            self.game_room_id, player_id
        )
        if data["destroyed_because"]:
            await self.emit("destroyed", data)
        else:
            await emit_update_room(
                data=data,
                game_room_id=self.game_room_id,
                player_id_list=player_id_list,
                sid_list=sid_list,
            )

    async def on_start(self, sid, data):
        # self.emit("my_response", data)
        await game_start(self.game_room_id)
        data = await update_or_create_matchs_list(self.match_dict, self.game_room_id)
        await emit_update_tournament(data=data, game_room_id=self.game_room_id)

import asyncio
import socketio
from .databaseio import left_game_room, game_start, update_or_create_matchs_list
from socketcontrol.events import sio


async def emit_update_room(data, game_room_id, player_id_list, sid_list):
    for sid in sid_list:
        copy_data = data.copy()
        copy_data["my_player_id"] = player_id_list[sid_list.index(sid)]
        await sio.emit(
            "update_room", copy_data, room=sid, namespace=f"/game/room/{game_room_id}"
        )


async def emit_destroyed(data, game_room_id):
    await sio.emit("destroyed", data, namespace=f"/game/room/{game_room_id}")


async def emit_update_tournament(data, game_room_id):
    await sio.emit("update_tournament", data, namespace=f"/game/room/{game_room_id}")


class GameRoomNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace, game_room_id):
        super().__init__(namespace=namespace)
        self.game_room_id = game_room_id
        self.match_dict = {}
        print(f"game room namespace ##{self.game_room_id}## created")

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

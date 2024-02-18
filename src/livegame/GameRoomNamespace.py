import random
import math
import time
from typing import Dict, List

import socketio

from accounts.models import User
from game.models import GamePlayer, Game, GameRoom
from .databaseio import left_game_room, game_start
from socketcontrol.events import sio
from socketcontrol.events import get_user_by_token
from asgiref.sync import sync_to_async
from livegame.SubGameConfig import SubGameConfig, get_default_subgame_config


def is_power_of_two(n: int) -> bool:
    """
    - A power of two in binary has a single '1' followed by '0's.
    - Subtracting one from this number flips all the bits up to
      the first '1', including the '1' itself.
    - The bitwise AND of these two numbers will have no bits in
      common and hence will result in zero.
    """
    return n > 1 and (n & (n - 1)) == 0


@sync_to_async
def update_game_room_sid(user, sid):
    user.socket_session.game_room_session_id = sid
    user.socket_session.save()


class GameRoomNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace, game_room_id):
        super().__init__(namespace=namespace)
        self.game_room_id = game_room_id
        self.host_user = GameRoom.objects.get(id=game_room_id).host

        # sid: {{"intra_id": <String>, "nickname": <String>, "avatar": <String>}}
        self.sid_to_user_data = {}
        self.match_dict = {}

        self.n_players = -1
        self.n_ranks = -1
        self.rank_ongoing = -1
        # [ [ {"sid_a": str | None, "sid_b": str | None, "winner": str | None} ] ]
        # sid_a, sid_b = sid | None, winner = "A" | "B" | None
        self.tournament_tree: List[List[dict]] = []

        # config value hardcoded for now
        self.config = get_default_subgame_config()
        print(f"game room namespace ##{self.game_room_id}## created")

    # SIO: F>B connect
    async def on_connect(self, sid, environ):
        try:
            cookies = environ.get("HTTP_COOKIE", "")
            cookie_dict = dict(
                item.split("=") for item in cookies.split("; ") if "=" in item
            )
            token = cookie_dict.get("kimyeonhkimbabo_token", None)

            if not token:
                print("No token")
                await self.disconnect(sid)

            user: User = await get_user_by_token(token)
            await update_game_room_sid(user, sid)

            self.sid_to_user_data[sid] = {
                "intra_id": user.intra_id,
                "nickname": user.profile.nickname,
                "avatar": user.profile.avatar,
            }

        except Exception as e:
            print(f"Error in connect: {e}")
            await self.disconnect(sid)

    # SIO: F>B exited
    async def on_exited(self, sid, data):
        del self.sid_to_user_data[sid]

        player_id = data["my_player_id"]
        data, player_id_list, sid_list = await left_game_room(
            self.game_room_id, player_id
        )
        if data.get("destroyed_because", None):
            await self.emit("destroyed", data)
            return

        await self.emit_update_room(data, player_id_list, sid_list)

    # SIO: F>B start
    async def on_start(self, sid, data):
        await game_start(self.game_room_id)

        self.build_tournament_tree()
        await self.emit_update_tournament()

        while True:
            # TODO: 현재 rank_ongoing에 대해 n개 SubGameSession 생성
            # TODO: n초 후 모든 SubGameSession 시작 (start, emit_config)
            # TODO: 한 SubGameSession이 끝나면 self.tournament_tree 업데이트 및 self.emit_update_tournament()
            # TODO: 모든 SubGameSession 끝나기 기다림
            if self.is_current_rank_done():
                self.rank_ongoing -= 1
            await self.emit_update_tournament()
            break

    def is_current_rank_done(self) -> bool:
        # TODO: implement
        # self.tournament_tree 순회하며 모든 SubGame의 "winner"값이 정해졌을 시 True
        pass

    def get_sid_from_intra_id(self, sid) -> str:
        for sid_key, user_data in self.sid_to_user_data.items():
            if sid_key == sid:
                return user_data["intra_id"]
        raise ValueError(f"{sid} not found in GameRoomNamespace {self.namespace}")

    def build_tournament_tree(self):
        game_room = GameRoom.objects.get(pk=self.game_room_id)
        game = game_room.game
        players: List[GamePlayer] = list(game.game_player.all().order_by("id"))
        self.n_players = len(players)
        random.shuffle(players)

        if not is_power_of_two(self.n_players):
            raise ValueError(f"Invalid number of players {self.n_players}")

        self.n_ranks = int(math.log2(self.n_players))
        self.rank_ongoing = self.n_ranks - 1
        self.tournament_tree = [[] for _ in range(self.n_ranks)]

        for idx_rank in range(self.n_ranks):  # 0, 1, 2...
            # 0 -> (0..1), 1 -> (0..2)
            for _ in range(int(math.pow(2, idx_rank))):
                subgame_repr = {
                    "sid_a": None,
                    "sid_b": None,
                    "winner": None,
                }
                self.tournament_tree[idx_rank].append(subgame_repr)

        if int(math.pow(2, self.n_ranks - 1)) != self.n_players / 2:
            raise ValueError(
                f"Error while building tournament tree: n_players / 2 {self.n_players / 2} != int(math.pow(2, self.n_ranks - 1)) {int(math.pow(2, self.n_ranks - 1))}"
            )

        for idx_in_rank in range(self.n_players / 2):
            # idx_in_rank = 0    | 1    | 2    | 3
            # idx player  = 0, 1 | 2, 3 | 4, 5 | 6, 7
            subgame_item = self.tournament_tree[self.n_ranks - 1][idx_in_rank]
            idx_player_a = idx_in_rank * 2 + 0
            idx_player_b = idx_in_rank * 2 + 1
            intra_id_a = players[idx_player_a].user.intra_id
            intra_id_b = players[idx_player_b].user.intra_id
            subgame_item["sid_a"] = self.get_sid_from_intra_id(intra_id_a)
            subgame_item["sid_b"] = self.get_sid_from_intra_id(intra_id_b)

    async def emit_update_room(self, data, player_id_list, sid_list):
        for sid in sid_list:
            copy_data = data.copy()
            copy_data["my_player_id"] = player_id_list[sid_list.index(sid)]
            await sio.emit("update_room", data, room=sid, namespace=self.namespace)

    async def emit_destroyed(self, data):
        # SIO: B>F destroyed
        await sio.emit("destroyed", data, namespace=self.namespace)

    def get_subgame_repr(self, subgame_info_with_sid: dict) -> dict:
        result = {}

        if subgame_info_with_sid["sid_a"] is None:
            result["player_a"] = None
        else:
            result["player_a"] = self.sid_to_user_data[subgame_info_with_sid["sid_a"]]

        if subgame_info_with_sid["sid_b"] is None:
            result["player_b"] = None
        else:
            result["player_b"] = self.sid_to_user_data[subgame_info_with_sid["sid_b"]]

        result["winner"] = subgame_info_with_sid["winner"]

        return result

    def get_subgames_repr(self) -> List[List[dict]]:
        result = []
        for subgame_in_rank in self.tournament_tree:
            result.append([])
            for subgame in subgame_in_rank:
                result.append(self.get_subgame_repr(subgame))

    async def emit_update_tournament(self):
        # SIO: B>F update_tournament
        data = {
            "t_event": time.time(),
            "n_ranks": self.n_ranks,
            "rank_ongoing": self.rank_ongoing,
            "subgames": self.get_subgames_repr(),
        }
        await sio.emit("update_tournament", data, namespace=self.namespace)


GAMEROOMNAMESPACE_REGISTRY: Dict[int, GameRoomNamespace] = {}

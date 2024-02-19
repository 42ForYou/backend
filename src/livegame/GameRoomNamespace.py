import random
import math
import time
import asyncio
from typing import Dict, List

import socketio

from accounts.models import User, UserDataCache, fetch_user_data_cache
from game.models import Game, GamePlayer, GameRoom
from .databaseio import left_game_room, game_start
from socketcontrol.events import sio
from socketcontrol.events import get_user_by_token
from asgiref.sync import sync_to_async
from livegame.SubGameSession.SubGameSession import SubGameSession
from livegame.SubGameSession.PaddleStatus import Player
from livegame.SubGameResult import SubGameResult
from livegame.SubGameConfig import get_default_subgame_config


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
    def __init__(self, game: Game):
        super().__init__(namespace=f"/game/room/{game.game_room.id}")
        self.game_room_id = game.game_room.id
        self.host_user = game.game_room.host

        self.sid_to_user_data: Dict[str, UserDataCache] = {}
        self.match_dict = {}

        self.users_cache: List[UserDataCache] = []
        self.n_players = -1
        self.n_ranks = -1
        self.rank_ongoing = -1
        self.tournament_tree: List[List[SubGameResult]] = []

        # config value hardcoded for now
        self.config = get_default_subgame_config(game)
        print(f"game room namespace ##{self.game_room_id}## created")

    # SIO: F>B connect
    async def on_connect(self, sid, environ):
        try:
            cookies = environ.get("HTTP_COOKIE", "")
            cookie_dict = dict(
                item.split("=") for item in cookies.split("; ") if "=" in item
            )
            token = cookie_dict.get("pong_token", None)

            if not token:
                print("No token")
                await self.disconnect(sid)

            user: User = await get_user_by_token(token)
            await update_game_room_sid(user, sid)

            self.sid_to_user_data[sid] = await fetch_user_data_cache(user)

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
        if not self.is_host(sid):
            print(
                f"Player pressing start button is not host: {sid} ({self.sid_to_user_data[sid]})"
            )
            return

        await game_start(self.game_room_id)

        await self.build_tournament_tree()
        await self.emit_update_tournament()

        while self.rank_ongoing >= 0:
            for idx_in_rank, subgame_item in enumerate(
                self.tournament_tree[self.rank_ongoing]  # 이번 rank의 SubGameResult들
            ):
                player_data_a = self.sid_to_user_data[subgame_item.sid_a]
                player_data_b = self.sid_to_user_data[subgame_item.sid_b]
                subgame_item.session = SubGameSession(
                    config=self.config,
                    gameroom_namespace=self,
                    intra_id_a=player_data_a.intra_id,
                    intra_id_b=player_data_b.intra_id,
                    idx_rank=self.rank_ongoing,
                    idx_in_rank=idx_in_rank,
                    # TODO: implement random ball direction
                    ball_init_dx=math.sqrt(2) * self.config.v_ball,
                    ball_init_dy=math.sqrt(2) * self.config.v_ball,
                )
                sio.register_namespace(subgame_item.session)
                # SIO: B>F config
                await subgame_item.session.emit_config()

            await asyncio.sleep(self.config.time_before_start)

            await asyncio.gather(
                *[  # update winner & emit update tournament happens inside subgameresult
                    subgameresult.session.start()
                    for subgameresult in self.tournament_tree[self.rank_ongoing]
                ]
            )

            # TODO: delete in production
            if not self.is_current_rank_done():
                raise Exception(f"Logic error: current rank is not done...")

            # 이번 rank의 SubGameResult들 un-register
            for subgame_item in self.tournament_tree[self.rank_ongoing]:
                sio.namespace_handlers.pop(subgame_item.session.namespace)

            self.rebuild_tournament_tree(self.rank_ongoing, self.rank_ongoing - 1)

            print(f"Current rank {self.rank_ongoing} is finished")
            self.rank_ongoing -= 1
            print(f"rank_ongoing decrease to {self.rank_ongoing}")

        print(f"GameRoom finished.")

    # TODO: delete in production
    def is_current_rank_done(self) -> bool:
        winners = [item.winner for item in self.tournament_tree[self.rank_ongoing]]
        return all([winner_val is not None for winner_val in winners])

    def get_sid_from_intra_id(self, intra_id) -> str:
        for sid_key, user_data in self.sid_to_user_data.items():
            if user_data.intra_id == intra_id:
                return sid_key
        raise ValueError(f"{intra_id} not found in GameRoomNamespace {self.namespace}")

    def is_host(self, sid) -> bool:
        if sid not in self.sid_to_user_data:
            return False

        host_intra = self.sid_to_user_data[sid].intra_id
        return host_intra == self.host_user.intra_id

    @sync_to_async
    def build_tournament_tree(self):
        game_room = GameRoom.objects.get(pk=self.game_room_id)
        game = game_room.game
        players: List[GamePlayer] = list(game.game_player.all().order_by("id"))

        self.users_cache = [
            UserDataCache(
                game_player.user.intra_id,
                game_player.user.profile.nickname,
                game_player.user.profile.avatar,
            )
            for game_player in players
        ]
        self.n_players = len(self.users_cache)
        random.shuffle(self.users_cache)

        if not is_power_of_two(self.n_players):
            raise ValueError(f"Invalid number of players {self.n_players}")

        self.n_ranks = int(math.log2(self.n_players))
        self.rank_ongoing = self.n_ranks - 1
        self.tournament_tree = [[] for _ in range(self.n_ranks)]

        # fill empty values for all subgames
        for idx_rank in range(self.n_ranks):  # 0, 1, 2...
            # 0 -> (0..1), 1 -> (0..2)
            for _ in range(int(math.pow(2, idx_rank))):
                self.tournament_tree[idx_rank].append(
                    SubGameResult(None, None, None, None)
                )

        if int(math.pow(2, self.n_ranks - 1)) != self.n_players / 2:
            raise ValueError(
                f"Error while building tournament tree: n_players / 2 {self.n_players / 2} != int(math.pow(2, self.n_ranks - 1)) {int(math.pow(2, self.n_ranks - 1))}"
            )

        # fill actual determined values for subgames in the lowest rank
        for idx_in_rank in range(self.n_players // 2):
            # idx_in_rank = 0    | 1    | 2    | 3
            # idx player  = 0, 1 | 2, 3 | 4, 5 | 6, 7
            subgame_result = self.tournament_tree[self.n_ranks - 1][idx_in_rank]
            idx_player_a = idx_in_rank * 2 + 0
            idx_player_b = idx_in_rank * 2 + 1
            intra_id_a = self.users_cache[idx_player_a].intra_id
            intra_id_b = self.users_cache[idx_player_b].intra_id
            subgame_result.sid_a = self.get_sid_from_intra_id(intra_id_a)
            subgame_result.sid_b = self.get_sid_from_intra_id(intra_id_b)

    def rebuild_tournament_tree(self, rank_curr: int, rank_next: int) -> None:
        if rank_curr == 0:  # 결승이 끝났을땐 rebuild 불가
            return

        for idx_in_rank_next in range(int(math.pow(2, rank_next))):
            idx_in_rank_curr_l = idx_in_rank_next * 2 + 0
            idx_in_rank_curr_r = idx_in_rank_next * 2 + 1

            sid_winner_l = self.tournament_tree[rank_curr][
                idx_in_rank_curr_l
            ].get_sid_of_winner()
            sid_winner_r = self.tournament_tree[rank_curr][
                idx_in_rank_curr_r
            ].get_sid_of_winner()

            self.tournament_tree[rank_next][idx_in_rank_next].sid_a = sid_winner_l
            self.tournament_tree[rank_next][idx_in_rank_next].sid_b = sid_winner_r

    async def report_end_of_subgame(
        self, idx_rank: int, idx_in_rank: int, winner: Player
    ):
        self.tournament_tree[idx_rank][idx_in_rank].winner = winner.name
        print(f"rank {idx_in_rank} idx {idx_in_rank} winnder is {winner.name}")

        await self.emit_update_tournament()

    async def emit_update_room(self, data, player_id_list, sid_list):
        for sid in sid_list:
            copy_data = data.copy()
            copy_data["my_player_id"] = player_id_list[sid_list.index(sid)]
            await sio.emit("update_room", data, room=sid, namespace=self.namespace)

    async def emit_destroyed(self, data):
        # SIO: B>F destroyed
        await sio.emit("destroyed", data, namespace=self.namespace)

    def get_subgames_json(self) -> List[List[dict]]:
        return [
            [subgame.to_json(self.sid_to_user_data) for subgame in subgame_in_rank]
            for subgame_in_rank in self.tournament_tree
        ]

    async def emit_update_tournament(self):
        # SIO: B>F update_tournament
        data = {
            "t_event": time.time(),
            "n_ranks": self.n_ranks,
            "rank_ongoing": self.rank_ongoing,
            "subgames": self.get_subgames_json(),
        }
        await sio.emit("update_tournament", data, namespace=self.namespace)


GAMEROOMNAMESPACE_REGISTRY: Dict[int, GameRoomNamespace] = {}

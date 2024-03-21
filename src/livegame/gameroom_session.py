import random
import math
import asyncio
import logging
from typing import Dict, List
from enum import Enum

import socketio
from asgiref.sync import sync_to_async

from pong import settings
from accounts.models import User, UserDataCache, fetch_user_data_cache
from game.models import Game, GamePlayer, GameRoom, SubGame
from socketcontrol.events import sio
from socketcontrol.events import get_user_by_token
from .databaseio import left_game_room, get_room_data
from .precision_config import get_time
from .SubGameSession.subgame_session import SubGameSession
from .SubGameSession.Paddle import Player
from .subgame_result import SubGameResult
from .subgame_config import get_default_subgame_config
from .SubGameSession.sio_adapter import serialize_subgame_config


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


class SubGameSessionResult(Enum):
    OK = 0
    TIMEOUT = 1
    INTERNAL_ERROR = 2


def get_cause_of_termination(results: List[SubGameSessionResult]) -> str:
    for result in results:
        if result == SubGameSessionResult.INTERNAL_ERROR:
            return "internal_error"
        if result == SubGameSessionResult.TIMEOUT:
            return "connection_lost"

    raise ValueError(f"given results {results} doesn't contain not-ok result")


class GameRoomSession(socketio.AsyncNamespace):
    def __init__(self, game: Game):
        super().__init__(namespace=f"/game/room/{game.game_room.id}")
        self.logger = logging.getLogger(
            f"{__package__}.{__class__.__name__}.{game.game_room.id}"
        )

        self.game = game
        self.game_room_id = game.game_room.id
        self.host_user = game.game_room.host
        self.is_playing = False

        self.sid_to_user_data: Dict[str, UserDataCache] = {}

        self.users_cache: List[UserDataCache] = []
        self.n_players = -1
        self.n_ranks = -1
        self.rank_ongoing = -1
        self.tournament_tree: List[List[SubGameResult]] = []

        # config value hardcoded for now
        self.config = get_default_subgame_config(game)
        self.logger.info(f"Created {self.__class__.__name__} {self.namespace} created")

    # SIO: F>B connect
    async def on_connect(self, sid, environ):
        self.logger.debug(f"connect from sid {sid}")
        try:
            cookies = environ.get("HTTP_COOKIE", "")
            cookie_dict = dict(
                item.split("=") for item in cookies.split("; ") if "=" in item
            )
            token = cookie_dict.get(settings.SIMPLE_JWT["AUTH_COOKIE"], None)

            if not token:
                self.logger.warning("No token")
                await self.disconnect(sid)

            user: User = await get_user_by_token(token)
            await update_game_room_sid(user, sid)

            self.sid_to_user_data[sid] = await fetch_user_data_cache(user)

            self.logger.debug(f"sid_to_user_data: {self.sid_to_user_data}")
        except Exception as e:
            self.logger.error(f"Error in connect: {e}")
            await self.disconnect(sid)

    async def on_disconnect(self, sid):
        self.logger.debug(f"disconnect from sid {self.sid_to_user_data[sid].intra_id}")

        if not self.is_playing:
            del self.sid_to_user_data[sid]
            return

    # SIO: F>B entered
    async def on_entered(self, sid, data):
        self.logger.debug(
            f"entered {self.namespace} from sid {self.sid_to_user_data[sid].intra_id}"
        )

        data, sid_list, player_id_list, am_i_host_list = await get_room_data(
            self.game_room_id
        )
        await self.emit_update_room(data, player_id_list, sid_list, am_i_host_list)

    # SIO: F>B exited
    async def on_exited(self, sid, data):
        self.logger.debug(f"exited from sid {sid}")

        if self.is_playing:
            self.logger.warning(
                f"Player exiting while game is playing: {sid} ({self.sid_to_user_data[sid]})"
            )
            return

        intra_id = self.sid_to_user_data[sid].intra_id
        del self.sid_to_user_data[sid]

        data, player_id_list, sid_list, am_i_host_list = await left_game_room(
            self.game_room_id, intra_id
        )

        if data.get("destroyed_because", None):
            await self.emit("destroyed", data)
            return

        await self.emit_update_room(data, player_id_list, sid_list, am_i_host_list)

    async def start_subgame(self, subgame: SubGameSession) -> SubGameSessionResult:
        try:
            await subgame.start()
            return SubGameSessionResult.OK
        except TimeoutError as e:
            self.logger.error(f"Connection lost while running subgame {subgame}: {e}")
            return SubGameSessionResult.TIMEOUT
        except Exception as e:
            self.logger.error(f"Exception while running subgame {subgame}: {e}")
            return SubGameSessionResult.INTERNAL_ERROR

    # SIO: F>B start
    async def on_start(self, sid, _):
        self.logger.info(f"start from sid {sid}")
        if not self.is_host(sid):
            self.logger.warning(
                f"Player pressing start button is not host: {sid} ({self.sid_to_user_data[sid]})"
            )
            return

        await self.game_start()

        # SIO: B>F config
        await self.emit_config()

        await self.build_tournament_tree()
        await self.emit_update_tournament()

        while self.rank_ongoing >= 0:
            for idx_in_rank, subgame_result in enumerate(
                self.tournament_tree[self.rank_ongoing]  # 이번 rank의 SubGameResult들
            ):
                player_data_a = self.sid_to_user_data[subgame_result.sid_a]
                player_data_b = self.sid_to_user_data[subgame_result.sid_b]
                subgame_result.session = SubGameSession(
                    config=self.config,
                    gameroom_session=self,
                    intra_id_a=player_data_a.intra_id,
                    intra_id_b=player_data_b.intra_id,
                    idx_rank=self.rank_ongoing,
                    idx_in_rank=idx_in_rank,
                )
                sio.register_namespace(subgame_result.session)

            self.logger.debug(f"sleeping {self.config.t_delay_rank_start} seconds...")
            await asyncio.sleep(self.config.t_delay_rank_start)

            self.logger.debug(
                f"wait until all SubGameSession ends in rank {self.rank_ongoing}"
            )
            session_results = await asyncio.gather(
                *[  # update winner & emit update tournament happens inside subgameresult
                    self.start_subgame(subgameresult.session)
                    for subgameresult in self.tournament_tree[self.rank_ongoing]
                ]
            )

            if any(result != SubGameSessionResult.OK for result in session_results):
                self.logger.warning("GameRoomSession terminate")
                await self.emit_destroyed(get_cause_of_termination(session_results))
                await sync_to_async(self.game.delete)()
                return

            # TODO: delete in production
            if not self.is_current_rank_done():
                raise Exception("Logic error: current rank is not done...")

            self.logger.debug(f"sleeping {self.config.t_delay_rank_end} seconds...")
            await asyncio.sleep(self.config.t_delay_rank_end)

            for subgame_result in self.tournament_tree[self.rank_ongoing]:
                # 시작 - 종료 시간 반영
                subgame_result.t_start = subgame_result.session.t_start
                subgame_result.t_end = subgame_result.session.t_end
                # 이번 rank의 SubGameResult들 un-register
                sio.namespace_handlers.pop(subgame_result.session.namespace)

            self.update_tournament_tree(self.rank_ongoing, self.rank_ongoing - 1)

            self.logger.debug(f"Current rank {self.rank_ongoing} is finished")
            self.rank_ongoing -= 1
            self.logger.debug(f"rank_ongoing decrease to {self.rank_ongoing}")

            await self.emit_update_tournament()

        self.logger.debug("Update database...")
        await self.update_database()

        self.logger.info("GameRoom finished.")

    @sync_to_async
    def update_database(self):
        # game_room delete
        GameRoom.objects.get(pk=self.game_room_id).delete()
        # save subgame result
        for rank in self.tournament_tree:
            for subgame_result in rank:
                player_a_intra_id = self.sid_to_user_data[subgame_result.sid_a].intra_id
                player_b_intra_id = self.sid_to_user_data[subgame_result.sid_b].intra_id
                player_a = GamePlayer.objects.get(
                    user__intra_id=player_a_intra_id, game=self.game
                )
                player_b = GamePlayer.objects.get(
                    user__intra_id=player_b_intra_id, game=self.game
                )
                SubGame.objects.create(
                    game=self.game,
                    rank=subgame_result.session.idx_rank,
                    idx_in_rank=subgame_result.session.idx_in_rank,
                    player_a=player_a,
                    player_b=player_b,
                    point_a=subgame_result.session.paddles[Player.A].score,
                    point_b=subgame_result.session.paddles[Player.B].score,
                    winner=subgame_result.winner,
                    t_start=subgame_result.t_start,
                    t_end=subgame_result.t_end,
                )
                if subgame_result.winner == "A":
                    player_a.rank = subgame_result.session.idx_rank - 1
                    player_b.rank = subgame_result.session.idx_rank
                else:
                    player_a.rank = subgame_result.session.idx_rank
                    player_b.rank = subgame_result.session.idx_rank - 1
                self.logger.debug(
                    f"subgame rank {subgame_result.session.idx_rank}, "
                    f"winner: {subgame_result.winner}, "
                    f"player_a: {player_a.rank}, player_b: {player_b.rank}"
                )
                player_a.save()
                player_b.save()
                self.game.users.add(player_a.user)
                self.game.users.add(player_b.user)

    # TODO: delete in production
    def is_current_rank_done(self) -> bool:
        winners = [item.winner for item in self.tournament_tree[self.rank_ongoing]]
        return all(winner_val is not None for winner_val in winners)

    def get_sid_from_intra_id(self, intra_id) -> str:
        for sid_key, user_data in self.sid_to_user_data.items():
            if user_data.intra_id == intra_id:
                return sid_key
        raise ValueError(f"{intra_id} not found in GameRoomSession {self.namespace}")

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
        random.seed()
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
                self.tournament_tree[idx_rank].append(SubGameResult(self))

        if int(math.pow(2, self.n_ranks - 1)) != self.n_players / 2:
            raise ValueError(
                f"Error while building tournament tree: "
                f"n_players / 2 {self.n_players / 2} != int(math.pow(2, self.n_ranks - 1)) "
                f"{int(math.pow(2, self.n_ranks - 1))}"
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
            subgame_result.user_data_a = self.users_cache[idx_player_a]
            subgame_result.user_data_b = self.users_cache[idx_player_b]

    def update_tournament_tree(self, rank_curr: int, rank_next: int) -> None:
        if rank_curr == 0:  # 결승이 끝났을땐 rebuild 불가
            return

        for idx_in_rank_next in range(int(math.pow(2, rank_next))):
            idx_in_rank_curr_l = idx_in_rank_next * 2 + 0
            idx_in_rank_curr_r = idx_in_rank_next * 2 + 1

            sg_result_curr_l = self.tournament_tree[rank_curr][idx_in_rank_curr_l]
            sg_result_curr_r = self.tournament_tree[rank_curr][idx_in_rank_curr_r]

            sg_result_next = self.tournament_tree[rank_next][idx_in_rank_next]

            if sg_result_curr_l.winner:
                sg_result_next.sid_a = sg_result_curr_l.get_sid_of_winner()
                sg_result_next.user_data_a = sg_result_curr_l.get_user_data_of_winner()

            if sg_result_curr_r.winner:
                sg_result_next.sid_b = sg_result_curr_r.get_sid_of_winner()
                sg_result_next.user_data_b = sg_result_curr_r.get_user_data_of_winner()

    async def report_winner_of_subgame(
        self, idx_rank: int, idx_in_rank: int, winner: Player
    ):
        self.tournament_tree[idx_rank][idx_in_rank].winner = winner.name
        if idx_rank == 0:
            return

        self.update_tournament_tree(self.rank_ongoing, self.rank_ongoing - 1)
        await self.emit_update_tournament()

    async def emit_update_room(
        self, data, player_id_list, sid_list, am_i_host_list
    ) -> None:
        for sid in sid_list:
            copy_data = data.copy()
            copy_data["my_player_id"] = player_id_list[sid_list.index(sid)]
            copy_data["am_i_host"] = am_i_host_list[sid_list.index(sid)]
            await sio.emit("update_room", copy_data, room=sid, namespace=self.namespace)
            self.logger.debug(f"emit update_room: {copy_data}")

    async def emit_destroyed(self, cause):
        data = {"t_event": get_time(), "destroyed_because": cause}
        # SIO: B>F destroyed
        await sio.emit("destroyed", data, namespace=self.namespace)
        self.logger.debug(f"emit destroyed: {data}")

    async def emit_update_tournament(self):
        # SIO: B>F update_tournament
        data = {
            "t_event": get_time(),
            "n_ranks": self.n_ranks,
            "rank_ongoing": self.rank_ongoing,
            "subgames": [
                [subgame.to_dict() for subgame in subgame_in_rank]
                for subgame_in_rank in self.tournament_tree
            ],
        }
        await sio.emit("update_tournament", data, namespace=self.namespace)
        self.logger.debug(f"emit update tournament: {data}")

    async def emit_config(self) -> None:
        event = "config"
        data = {"t_event": get_time(), "config": serialize_subgame_config(self.config)}
        # SIO: B>F config
        await sio.emit(event, data=data, namespace=self.namespace)
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

    @sync_to_async
    def game_start(self):
        game_room = self.game.game_room
        game_room.is_playing = True
        game_room.join_players = self.game.n_players
        game_room.save()
        self.is_playing = True


GAMEROOMSESSION_REGISTRY: Dict[int, GameRoomSession] = {}

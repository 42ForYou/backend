import time
import asyncio
from typing import Dict, Tuple, List

from socketcontrol.events import sio
from livegame.GameSession import GameSession
from livegame.PaddleStatus import Player
from livegame.GameSessionSIOAdapter import GameSessionSIOAdapter

# TODO: Replace print() statements with proper logging module


# TODO: Replace with setting values from DB
class DummyGameSessionInitValue:
    width = 800
    height = 600
    epsilon = 0.1
    paddle_len = 50
    paddle_speed = 200
    ball_init_dx = 100
    ball_init_dy = 100
    time_limit = 60


class GameSessionRegistry:
    registry: Dict[int, Dict[int, Dict[int, GameSessionSIOAdapter]]] = {}

    @staticmethod
    def register(room_id: int, rank: int, idx_in_rank: int) -> GameSessionSIOAdapter:
        root_reg = GameSessionRegistry.registry
        if room_id not in root_reg:
            root_reg[room_id] = {}

        room_reg = root_reg[room_id]
        if rank not in room_reg:
            room_reg[rank] = {}

        rank_reg = room_reg[rank]
        if idx_in_rank in rank_reg:
            raise ValueError(
                f"GameSession for room {room_id} rank {rank} idx {idx_in_rank} already exists"
            )

        session = GameSession(
            DummyGameSessionInitValue.width,
            DummyGameSessionInitValue.height,
            DummyGameSessionInitValue.epsilon,
            DummyGameSessionInitValue.paddle_len,
            DummyGameSessionInitValue.paddle_speed,
            DummyGameSessionInitValue.ball_init_dx,
            DummyGameSessionInitValue.ball_init_dy,
            DummyGameSessionInitValue.time_limit,
        )
        rank_reg[idx_in_rank] = GameSessionSIOAdapter(
            session, room_id, rank, idx_in_rank
        )
        print(
            f"Registered GameSessionSIOAdapter in room {room_id} rank {rank} idx {idx_in_rank}"
        )
        return rank_reg[idx_in_rank]

    @staticmethod
    def get(room_id: int, rank: int, idx_in_rank: int) -> GameSessionSIOAdapter:
        return GameSessionRegistry.registry[room_id][rank][idx_in_rank]

    @staticmethod
    def destroy(room_id: int, rank: int, idx_in_rank: int) -> None:
        del GameSessionRegistry.registry[room_id][rank][idx_in_rank]
        print(f"Destroyed GameSession in room {room_id} rank {rank} idx {idx_in_rank}")

    @staticmethod
    async def update() -> None:
        ended_indices: List[Tuple[int, int, int]] = []

        for room_id, room_reg in GameSessionRegistry.registry.items():
            for rank, rank_reg in room_reg.items():
                for idx, adapter in rank_reg.items():
                    await adapter.update()
                    if adapter.ended:
                        ended_indices.append((room_id, rank, idx))

        for ended_idx in ended_indices:
            del GameSessionRegistry.registry[ended_idx[0]][ended_idx[1]][ended_idx[2]]


def emit_start(room_id: int, rank: int, idx_in_rank: int):
    adapter = GameSessionRegistry.register(room_id, rank, idx_in_rank)
    gs = adapter.session

    event = "start"
    data = {
        "t_event": time.time(),
        "config": {
            "x_max": gs.config.x_max,
            "y_max": gs.config.y_max,
            "x_min": gs.config.x_min,
            "y_min": gs.config.y_min,
            "v_paddle": gs.config.v_paddle,
            "len_paddle": gs.paddles[Player.A].len,
            "v_ball": gs.config.v_ball,
        },
    }
    # SIO: B>F start
    sio.emit(event, data=data, namespace=adapter.sio_ns.namespace)
    print(f"Emit event {event} data {data} to namespace {adapter.sio_ns.namespace}")


async def update_game_session_registry_forever():
    # TODO: remove i
    i = 0
    while True:
        i += 1
        print(f"update_game_session_registry_forever {i}th times")
        await GameSessionRegistry.update()
        # TODO: adjust minimum sleep time by Literals
        await asyncio.sleep(1)

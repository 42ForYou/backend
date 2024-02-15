import socketio
import time
from typing import Dict

from pong.asgi import sio
from GameSession import GameSession
from BallTrack import BallTrack
from BallTrackSegment import BallTrackSegment
from PaddleStatus import PaddleStatus, KeyInput, Player

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
    registry: Dict[int, Dict[int, Dict[int, GameSession]]] = {}

    @staticmethod
    def register(room_id: int, rank: int, idx_in_rank: int) -> GameSession:
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

        rank_reg[idx_in_rank] = GameSession(
            DummyGameSessionInitValue.width,
            DummyGameSessionInitValue.height,
            DummyGameSessionInitValue.epsilon,
            DummyGameSessionInitValue.paddle_len,
            DummyGameSessionInitValue.paddle_speed,
            DummyGameSessionInitValue.ball_init_dx,
            DummyGameSessionInitValue.ball_init_dy,
            DummyGameSessionInitValue.time_limit,
        )
        print(f"Registered GameSession in room {room_id} rank {rank} idx {idx_in_rank}")
        return rank_reg[idx_in_rank]

    @staticmethod
    def get(room_id: int, rank: int, idx_in_rank: int) -> GameSession:
        return GameSessionRegistry.registry[room_id][rank][idx_in_rank]

    @staticmethod
    def destroy(room_id: int, rank: int, idx_in_rank: int) -> None:
        del GameSessionRegistry.registry[room_id][rank][idx_in_rank]
        print(f"Destroyed GameSession in room {room_id} rank {rank} idx {idx_in_rank}")


class SubGameNamespace(socketio.AsyncNamespace):
    def on_connect(self, sid, environ):
        print(f"Ns={self.namespace}, {sid} connected")
        # TODO: 접속한 유저가 대진표에서 어디에 있는지 파악 등,,,

    def on_disconnect(self, sid):
        print(f"Ns={self.namespace}, {sid} disconnected")
        # TODO: 나간 유저가 대진표에서 어디에 있는지 파악 등,,,

    def on_leave(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: leave, data={data}")
        # TODO: Impl

    def on_keyboard_input(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: keyboard_input, data={data}")
        # TODO: Impl

    @staticmethod
    def generate_namespace(room_id: int, rank: int, idx_in_rank: int) -> str:
        return f"/game/room/{room_id}/{rank}/{idx_in_rank}"


def emit_start(room_id: int, rank: int, idx_in_rank: int):
    gs = GameSessionRegistry.register(room_id, rank, idx_in_rank)

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
    ns = SubGameNamespace.generate_namespace(room_id, rank, idx_in_rank)
    sio.emit(event, data=data, namespace=ns)
    print(f"Emit event {event} data {data} to namespace {ns}")


def emit_update_time_left(room_id: int, rank: int, idx_in_rank: int):
    gs = GameSessionRegistry.get(room_id, rank, idx_in_rank)

    event = "update_time_left"
    data = {"t_event": time.time(), "time_left": gs.get_time_left()}
    ns = SubGameNamespace.generate_namespace(room_id, rank, idx_in_rank)
    sio.emit(event, data=data, namespace=ns)
    print(f"Emit event {event} data {data} to namespace {ns}")


def emit_ended(room_id: int, rank: int, idx_in_rank: int, winner: str):
    event = "ended"
    data = {"t_event": time.time(), "winner": winner}
    ns = SubGameNamespace.generate_namespace(room_id, rank, idx_in_rank)
    sio.emit(event, data=data, namespace=ns)
    print(f"Emit event {event} data {data} to namespace {ns}")


def emit_update_scores(
    room_id: int, rank: int, idx_in_rank: int, score_a: int, score_b: int
):
    event = "update_scores"
    data = {"t_event": time.time(), "score_a": score_a, "score_b": score_b}
    ns = SubGameNamespace.generate_namespace(room_id, rank, idx_in_rank)
    sio.emit(event, data=data, namespace=ns)
    print(f"Emit event {event} data {data} to namespace {ns}")


def serialize_balltracksegment(seg: BallTrackSegment):
    return {
        "x_s": seg.x_start,
        "y_s": seg.x_start,
        "x_e": seg.x_end,
        "y_e": seg.y_end,
        "dx": seg.dx,
        "dy": seg.dy,
    }


def serialize_balltrack(balltrack: BallTrack):
    return [serialize_balltracksegment(seg) for seg in balltrack.segments]


def emit_update_track_ball(
    room_id: int, rank: int, idx_in_rank: int, balltrack: BallTrack
):
    event = "update_track_ball"
    data = {
        "t_event": balltrack.t_start,
        "t_end": balltrack.t_end,
        "heading": balltrack.heading.name,
        "velocity": balltrack.v,
        "segments": serialize_balltrack(balltrack),
    }
    ns = SubGameNamespace.generate_namespace(room_id, rank, idx_in_rank)
    sio.emit(event, data=data, namespace=ns)
    print(f"Emit event {event} data {data} to namespace {ns}")


def emit_update_track_paddle():
    pass

import time

from pong.asgi import sio
from livegame.GameSession import GameSession
from livegame.PaddleStatus import Player, PaddleStatus
from livegame.BallTrack import BallTrack
from livegame.BallTrackSegment import BallTrackSegment
from livegame.SubGameNamespace import SubGameNamespace


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


class ValueUpdateManager:
    def __init__(self) -> None:
        self.initialized: bool = False

    # Update internal value to given one and returns True if given value is new.
    def update(self, new_val) -> bool:
        self.t_last_updated = time.time()

        if not self.initialized:
            self.val = new_val
            self.initialized = True
            return True

        is_new = self.val != new_val
        self.val = new_val
        return is_new


class GameSessionSIOAdapter:
    def __init__(
        self, session: GameSession, room_id: int, rank: int, idx_in_rank: int
    ) -> None:
        self.session = session
        self.room_id = room_id
        self.rank = rank
        self.idx_in_rank = idx_in_rank
        self.sio_ns = SubGameNamespace(f"/game/room/{room_id}/{rank}/{idx_in_rank}")
        sio.register_namespace(self.sio_ns)

        self.time_left = ValueUpdateManager()
        self.scores = ValueUpdateManager()
        self.balltrack = ValueUpdateManager()
        self.paddle_a = ValueUpdateManager()
        self.paddle_b = ValueUpdateManager()

        self.ended = False

    async def update(self) -> None:
        self.session.update()

        # TODO: implement ending in GameSession and activate
        # if self.session.ended():
        #     await self.emit_ended()
        #     self.ended = True
        #     return

        if self.time_left.update(self.session.get_time_left()):
            await self.emit_update_time_left()

        if self.scores.update(
            (self.session.paddles[Player.A].score, self.session.paddles[Player.B].score)
        ):
            await self.emit_update_scores()

        if self.paddle_a.update(self.session.paddles[Player.A]):
            await self.emit_update_track_paddle(self.paddle_a.val)

        if self.paddle_a.update(self.session.paddles[Player.B]):
            await self.emit_update_track_paddle(self.paddle_b.val)

    async def emit_update_time_left(self) -> None:
        event = "update_time_left"
        data = {
            "t_event": self.time_left.t_last_updated,
            "time_left": self.time_left.val,
        }
        await sio.emit(event, data=data, namespace=self.sio_ns.namespace)
        print(f"Emit event {event} data {data} to namespace {self.sio_ns.namespace}")

    async def emit_update_scores(self):
        event = "update_scores"
        data = {
            "t_event": self.scores.t_last_updated,
            "score_a": self.scores.val[0],
            "score_b": self.scores.val[1],
        }
        await sio.emit(event, data=data, namespace=self.sio_ns.namespace)
        print(f"Emit event {event} data {data} to namespace {self.sio_ns.namespace}")

    async def emit_update_track_ball(self):
        event = "update_track_ball"
        balltrack: BallTrack = self.balltrack.val
        data = {
            "t_event": balltrack.t_start,
            "t_end": balltrack.t_end,
            "heading": balltrack.heading.name,
            "velocity": balltrack.v,
            "segments": serialize_balltrack(balltrack),
        }
        await sio.emit(event, data=data, namespace=self.sio_ns.namespace)
        print(f"Emit event {event} data {data} to namespace {self.sio_ns.namespace}")

    async def emit_update_track_paddle(self, paddle: PaddleStatus):
        event = "update_track_paddle"
        data = {
            "t_event": paddle.t_last_updated,
            "player": paddle.player.name,
            "y": paddle.y,
            "dy": paddle.dy,
        }
        await sio.emit(event, data=data, namespace=self.sio_ns.namespace)
        print(f"Emit event {event} data {data} to namespace {self.sio_ns.namespace}")

    async def emit_ended(self):
        event = "ended"
        # TODO: when get_winner() gets implemented delete below
        data = {"t_event": time.time(), "winner": "A"}
        # data = {"t_event": time.time(), "winner": self.session.get_winner()}
        await sio.emit(event, data=data, namespace=self.sio_ns.namespace)
        print(f"Emit event {event} data {data} to namespace {self.sio_ns.namespace}")

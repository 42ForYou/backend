import time
import math
import asyncio
import socketio
from typing import Dict
from enum import Enum

from socketcontrol.events import sio
from livegame.SubGameConfig import SubGameConfig
from livegame.SubGameSession.PaddleStatus import PaddleStatus, KeyInput, Player
from livegame.SubGameSession.BallTrack import BallTrack
from livegame.SubGameSession.SIOAdapter import (
    serialize_balltrack,
    serialize_balltracksegment,
)


class TurnResult(Enum):
    DEFENDED = 0
    A_SCORED = 1
    B_SCORED = 1


# TODO: update print() statements to proper logging
class SubGameSession(socketio.AsyncNamespace):
    def __init__(
        self,
        namespace,
        config: SubGameConfig,
        ball_init_dx: float,
        ball_init_dy: float,
    ):
        super().__init__(namespace)

        self.config = config
        if self.config.flt_eq(ball_init_dx, 0.0):
            raise ValueError(f"SubGameSession got invalid dx {ball_init_dx}")

        self.paddles: Dict[Player, PaddleStatus] = {
            Player.A: PaddleStatus(self.config, Player.A, config.l_paddle),  # LEFT
            Player.B: PaddleStatus(self.config, Player.B, config.l_paddle),  # RIGHT
        }
        self.ball_init_dx = ball_init_dx
        self.ball_init_dy = ball_init_dy
        self.update_balltrack()
        self.started = False
        self.time_over = False
        self.winner = Player.NOBODY
        self.log(f"Created SubGameSession with {self.config}")

    def log(self, msg: str) -> None:
        print(f"{id(self)}: {msg}")

    # SIO: F>B connect
    def on_connect(self, sid, environ):
        print(f"Ns={self.namespace}, {sid} connected")
        # TODO: 접속한 유저가 대진표에서 어디에 있는지 파악 등,,,

    # SIO: F>B disconnect
    def on_disconnect(self, sid):
        print(f"Ns={self.namespace}, {sid} disconnected")
        # TODO: 나간 유저가 대진표에서 어디에 있는지 파악 등,,,

    # SIO: F>B leave
    async def on_leave(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: leave, data={data}")
        # TODO: Impl

    # SIO: F>B keyboard_input
    async def on_keyboard_input(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: keyboard_input, data={data}")
        if not self.started:
            return

        # TODO: activate below logic according to "data"
        # self.paddles[player].update_key(key_input)
        # self.paddles[player].update(time.time())

        # self.log(
        #     f"Update player {player.name} key to {key_input}, y={self.paddles[player].y} dy={self.paddles[player].dy}"
        # )
        # self.emit_update_track_paddle(self.paddles[??])
        pass

    def determine_winner(self, turn_result: TurnResult) -> None:
        if self.time_over:  # sudden death
            if turn_result == TurnResult.A_SCORED:
                self.winner = Player.A
            else:
                self.winner = Player.B
        elif self.paddles[Player.A].score == self.config.match_point:
            self.winner = Player.A
        elif self.paddles[Player.B].score == self.config.match_point:
            self.winner = Player.B

    # start simulation. start accepting key press.
    async def start(self) -> None:
        self.t_start = time.time()
        self.emit_update_time_left()
        self.started = True
        self.log(f"start simulation of SubGameSession at {self.t_start}")

        self.balltrack = BallTrack(
            self.config, 0, 0, self.ball_init_dx, self.ball_init_dy, self.t_start
        )
        self.log(f"start balltrack: {self.balltrack}")

        # run until score reaches matchpoint
        while True:
            # assign offense/defense players/paddles
            result = await self.update_balltrack()
            self.determine_winner(result)

            if self.winner != Player.NOBODY:
                await self.emit_ended()
                return

            # emit balltrack
            await self.emit_update_track_ball()

    def update_turns(self) -> None:
        if self.balltrack.heading == BallTrack.Heading.LEFT:
            self.paddle_offense = self.paddles[Player.A]
            self.paddle_defense = self.paddles[Player.B]
        else:
            self.paddle_offense = self.paddles[Player.B]
            self.paddle_defense = self.paddles[Player.A]

        print(
            f"{id(self)}: Attack: {self.paddle_offense.player.name} -> {self.paddle_offense.player.name}"
        )

    async def update_balltrack(self) -> TurnResult:
        self.update_turns()

        # await until ball hits the other side
        await asyncio.sleep(self.balltrack.t_duration)
        new_t = time.time()

        if new_t - self.t_start > self.config.t_limit:
            self.log("time is up")

        # only update defending paddle
        self.paddle_defense.update()
        if self.paddle_defense.hit(self.balltrack.y_impact):
            # success to defend, create reflection
            print(
                f"{id(self)}: Player {self.paddle_defense.player.name} reflects the ball"
            )
            new_x_start, new_y_start = self.balltrack.next_xy_start
            new_dx, new_dy = self.balltrack.next_dx_dy
            self.balltrack = BallTrack(
                self.config,
                new_x_start,
                new_y_start,
                new_dx,
                new_dy,
                new_t,
            )

            return TurnResult.DEFENDED
        else:
            # fail to defend, scoring, reset
            self.paddle_offense.score += 1
            print(
                f"{id(self)}: Player {self.paddle_offense.player.name} scores to {self.paddle_offense.score}"
            )
            new_dx, new_dy = self.balltrack.next_dx_dy
            self.balltrack = BallTrack(self.config, 0, 0, new_dx, new_dy, new_t)
            if self.paddle_offense.player == Player.A:
                return TurnResult.A_SCORED
            else:
                return TurnResult.B_SCORED

    async def emit_update_time_left(self) -> None:
        event = "update_time_left"
        data = {
            "t_event": time.time(),
            "time_left": self.get_time_left(),
        }
        # SIO: B>F update_time_left
        await sio.emit(event, data=data, namespace=self.namespace)
        print(f"Emit event {event} data {data} to namespace {self.namespace}")

    async def emit_update_scores(self):
        event = "update_scores"
        data = {
            "t_event": time.time(),
            "score_a": self.paddles[Player.A].score,
            "score_b": self.paddles[Player.B].score,
        }
        # SIO: B>F update_scores
        await sio.emit(event, data=data, namespace=self.namespace)
        print(f"Emit event {event} data {data} to namespace {self.namespace}")

    async def emit_update_track_ball(self):
        event = "update_track_ball"
        data = {
            "t_event": self.balltrack.t_start,
            "t_end": self.balltrack.t_end,
            "heading": self.balltrack.heading.name,
            "velocity": self.balltrack.v,
            "segments": serialize_balltrack(self.balltrack),
        }
        # SIO: B>F update_track_ball
        await sio.emit(event, data=data, namespace=self.namespace)
        print(f"Emit event {event} data {data} to namespace {self.namespace}")

    async def emit_update_track_paddle(self, paddle: PaddleStatus):
        event = "update_track_paddle"
        data = {
            "t_event": paddle.t_last_updated,
            "player": paddle.player.name,
            "y": paddle.y,
            "dy": paddle.dy,
        }
        # SIO: B>F update_track_paddle
        await sio.emit(event, data=data, namespace=self.namespace)
        print(f"Emit event {event} data {data} to namespace {self.namespace}")

    async def emit_ended(self):
        event = "ended"
        data = {"t_event": time.time(), "winner": self.winner.name}
        # SIO: B>F ended
        await sio.emit(event, data=data, namespace=self.namespace)
        print(f"Emit event {event} data {data} to namespace {self.namespace}")

    def get_time_left(self) -> int:
        time_now = time.time()
        return math.ceil(time_now - self.t_start)

    def __str__(self) -> str:
        return f"GameSession t_start={self.t_start}"
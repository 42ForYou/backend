import time
import math
import asyncio
import logging
from typing import Dict
from enum import Enum
import socketio

from accounts.models import User
from socketcontrol.events import sio, get_user_by_token
from ..SubGameConfig import SubGameConfig
from .PaddleStatus import PaddleStatus, KeyInput, Player
from .BallTrack import BallTrack
from .SIOAdapter import serialize_balltrack


class TurnResult(Enum):
    DEFENDED = 0
    A_SCORED = 1
    B_SCORED = 1


class SubGameSession(socketio.AsyncNamespace):
    def __init__(
        self,
        config: SubGameConfig,
        gameroom_session,
        intra_id_a: str,
        intra_id_b: str,
        idx_rank: int,
        idx_in_rank: int,
        ball_init_dx: float,
        ball_init_dy: float,
    ):
        super().__init__(f"{gameroom_session.namespace}/{idx_rank}/{idx_in_rank}")

        self.logger = logging.getLogger(
            f"{__package__}.{self.__class__.__name__}.{idx_rank}.{idx_in_rank}"
        )

        self.config = config
        if self.config.flt_eq(ball_init_dx, 0.0):
            raise ValueError(f"SubGameSession got invalid dx {ball_init_dx}")

        self.gr_session = gameroom_session
        self.idx_rank = idx_rank
        self.idx_in_rank = idx_in_rank

        self.paddles: Dict[Player, PaddleStatus] = {
            Player.A: PaddleStatus(self.config, Player.A, config.l_paddle),  # LEFT
            Player.B: PaddleStatus(self.config, Player.B, config.l_paddle),  # RIGHT
        }
        self.intra_id_a = intra_id_a
        self.intra_id_b = intra_id_b
        self.ball_init_dx = ball_init_dx
        self.ball_init_dy = ball_init_dy
        self.running = False
        self.time_over = False
        self.winner = Player.NOBODY
        self.sid_to_player = {}
        self.logger.info(f"Created SubGameSession with {self.config}")
        self.logger.debug(f"A: {intra_id_a}, B: {intra_id_b}")

    # SIO: F>B connect
    async def on_connect(self, sid, environ):
        self.logger.debug(f"connect from sid {sid}")
        try:
            cookies = environ.get("HTTP_COOKIE", "")
            cookie_dict = dict(
                item.split("=") for item in cookies.split("; ") if "=" in item
            )
            token = cookie_dict.get("pong_token", None)
            if not token:
                self.logger.warn("No token")
                await self.disconnect(sid)

            user: User = await get_user_by_token(token)

            if user.intra_id == self.intra_id_a:
                self.sid_to_player[sid] = Player.A
            elif user.intra_id == self.intra_id_b:
                self.sid_to_player[sid] = Player.B
            else:
                self.logger.warn(f"connected {user.intra_id} is not assigned player")
                await self.disconnect(sid)

        except Exception as e:
            self.logger.error(f"Error in connect: {e}")
            await self.disconnect(sid)

    # SIO: F>B disconnect
    def on_disconnect(self, sid):
        self.logger.debug(f"disconnect from sid {sid}")
        if sid in self.sid_to_player:
            del self.sid_to_player[sid]

    # SIO: F>B keyboard_input
    async def on_keyboard_input(self, sid, data):
        self.logger.debug(f"keyboard_input from sid {sid}, data={data}")

        if not self.running:
            self.logger.debug(f"SubGameSession is not running")
            return

        if not sid in self.sid_to_player:
            self.logger.warn(f"sid {sid} is not connected player")
            return

        player: Player = self.sid_to_player[sid]
        key_input = KeyInput(KeyInput.Key[data["key"]], KeyInput.Action[data["action"]])

        self.paddles[player].update_key(key_input)
        self.paddles[player].update(time.time())
        self.logger.debug(
            f"Update player {player.name} key to {key_input}, "
            f"y={self.paddles[player].y} dy={self.paddles[player].dy}"
        )

        self.emit_update_track_paddle(self.paddles[player])

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
        self.t_start = time.time() + self.config.t_delay_subgame_start
        await self.emit_start()
        await asyncio.sleep(self.config.t_delay_subgame_start)

        self.emit_update_time_left_until_end()
        self.running = True
        self.logger.debug(f"start simulation of SubGameSession at {self.t_start}")

        self.balltrack = BallTrack(
            self.config, 0, 0, self.ball_init_dx, self.ball_init_dy, self.t_start
        )
        self.logger.debug(f"start balltrack: {self.balltrack}")

        # run until score reaches matchpoint
        while True:
            # assign offense/defense players/paddles
            result = await self.update_balltrack()
            self.determine_winner(result)

            if self.winner != Player.NOBODY:
                await self.emit_ended()
                await self.gr_session.report_winner_of_subgame(
                    self.idx_rank, self.idx_in_rank, self.winner
                )
                self.running = False
                # TODO: disconnect all clients?
                return

            # emit balltrack
            await self.emit_update_track_ball()

    def update_turns(self) -> None:
        if self.balltrack.heading == BallTrack.Heading.LEFT:
            self.paddle_offense = self.paddles[Player.B]
            self.paddle_defense = self.paddles[Player.A]
        else:
            self.paddle_offense = self.paddles[Player.A]
            self.paddle_defense = self.paddles[Player.B]

        self.logger.debug(
            f"Attack: {self.paddle_offense.player.name} -> {self.paddle_defense.player.name}"
        )

    async def update_balltrack(self) -> TurnResult:
        self.update_turns()

        # await until ball hits the other side
        await asyncio.sleep(self.balltrack.t_duration)
        new_t = time.time()

        if new_t - self.t_start > self.config.t_limit:
            self.logger.debug("time is up")

        # only update defending paddle
        self.paddle_defense.update(new_t)
        if self.paddle_defense.hit(self.balltrack.y_impact):
            # success to defend, create reflection
            self.logger.debug(
                f"Player {self.paddle_defense.player.name} reflects the ball"
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

        # fail to defend, scoring, reset
        self.paddle_offense.score += 1
        self.logger.debug(f"Player {self.paddle_offense.player} scored")
        await self.emit_update_scores()
        self.logger.debug(
            f"Player {self.paddle_offense.player.name} scores to {self.paddle_offense.score}"
        )
        new_dx, new_dy = self.balltrack.next_dx_dy
        self.balltrack = BallTrack(self.config, 0, 0, new_dx, new_dy, new_t)
        if self.paddle_offense.player == Player.A:
            return TurnResult.A_SCORED

        return TurnResult.B_SCORED

    async def emit_start(self) -> None:
        event = "start"
        data = {"t_event": self.t_start}
        # SIO: B>F start
        await sio.emit(event, data=data, namespace=self.namespace)
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

    async def emit_update_time_left(self) -> int:
        event = "update_time_left"
        time_left = self.get_time_left()
        data = {
            "t_event": time.time(),
            "time_left": time_left,
        }
        # SIO: B>F update_time_left
        await sio.emit(event, data=data, namespace=self.namespace)
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )
        return time_left

    async def emit_update_time_left_until_end(self) -> None:
        while await self.emit_update_time_left() != 0:
            t_emit = time.time()
            t_next_emit = self.t_start
            while t_next_emit <= t_emit:
                t_next_emit += 1.0

            await asyncio.sleep(t_next_emit - t_emit)

    async def emit_update_scores(self):
        self.logger.debug(
            f"Emit score: A {self.paddles[Player.A].score} : {self.paddles[Player.B].score} B"
        )
        event = "update_scores"
        data = {
            "t_event": time.time(),
            "score_a": self.paddles[Player.A].score,
            "score_b": self.paddles[Player.B].score,
        }
        # SIO: B>F update_scores
        await sio.emit(event, data=data, namespace=self.namespace)
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

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
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

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
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

    async def emit_ended(self):
        event = "ended"
        data = {"t_event": time.time(), "winner": self.winner.name}
        # SIO: B>F ended
        await sio.emit(event, data=data, namespace=self.namespace)
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

    def get_time_left(self) -> int:
        time_now = time.time()
        return math.ceil(time_now - self.t_start)

    def __str__(self) -> str:
        return f"GameSession t_start={self.t_start}"

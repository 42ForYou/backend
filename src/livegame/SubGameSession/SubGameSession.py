import time
import math
import asyncio
import socketio
import logging
from typing import Dict
from enum import Enum

from pong.settings import LOGLEVEL_TRACE_ENABLE
from accounts.models import User
from socketcontrol.events import sio, get_user_by_token
from livegame.SubGameConfig import SubGameConfig
from livegame.SubGameSession.PaddleStatus import PaddleStatus, KeyInput, Player
from livegame.SubGameSession.BallTrack import BallTrack, get_random_dx_dy
from livegame.SubGameSession.SIOAdapter import serialize_balltrack
import pong.settings as settings


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
    ):
        super().__init__(f"{gameroom_session.namespace}/{idx_rank}/{idx_in_rank}")

        self.logger = logging.getLogger(
            f"{__package__}.{self.__class__.__name__}.{idx_rank}.{idx_in_rank}"
        )

        self.config = config

        self.gr_session = gameroom_session
        self.idx_rank = idx_rank
        self.idx_in_rank = idx_in_rank

        self.paddles: Dict[Player, PaddleStatus] = {
            Player.A: PaddleStatus(self.config, Player.A, config.l_paddle),  # LEFT
            Player.B: PaddleStatus(self.config, Player.B, config.l_paddle),  # RIGHT
        }
        self.intra_id_a = intra_id_a
        self.intra_id_b = intra_id_b
        self.running = False
        self.time_over = False
        self.winner = Player.NOBODY
        self.sid_to_player = {}
        self.logger.info(f"Created SubGameSession with {self.config}")
        self.logger.debug(f"A: {intra_id_a}, B: {intra_id_b}")

    def trace(self, msg: str) -> None:
        if LOGLEVEL_TRACE_ENABLE != "0":
            self.logger.debug(f"[TRACE] {msg}")

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

        if self.paddles[player].update_key(key_input, time.time()):
            self.logger.debug(
                f"Update player {player.name} key to {key_input}, y={self.paddles[player].y} dy={self.paddles[player].dy}"
            )
            await self.emit_update_track_paddle(self.paddles[player])

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
        self.t_end = self.t_start + self.config.t_limit
        await self.emit_start()
        await asyncio.sleep(self.config.t_delay_subgame_start)

        asyncio.create_task(self.emit_update_time_left_until_end())
        self.running = True
        self.logger.debug(f"start simulation of SubGameSession at {self.t_start}")

        new_x, new_y = get_random_dx_dy(self.config.v_ball, 20)
        self.balltrack = BallTrack(
            self.config,
            self.config.x_ball_init,
            self.config.y_ball_init,
            new_x,
            new_y,
            self.t_start,
        )
        self.logger.debug(f"start balltrack: {self.balltrack}")

        # run until score reaches matchpoint
        while True:
            # emit balltrack
            await self.emit_update_track_ball()
            # assign offense/defense players/paddles
            result = await self.wait_ball_travel()
            self.determine_winner(result)

            if self.winner != Player.NOBODY:  # winner determined
                self.t_end = time.time()
                await self.emit_ended()
                await self.gr_session.report_winner_of_subgame(
                    self.idx_rank, self.idx_in_rank, self.winner
                )
                self.running = False
                # TODO: disconnect all clients?
                return

            # winner not determined

            if result == TurnResult.DEFENDED:
                # success to defend, create reflection
                self.logger.debug(f"{self.paddle_defense.player.name} defense success")
                new_x_start, new_y_start = self.balltrack.next_xy_start
                new_dx, new_dy = self.balltrack.next_dx_dy(self.paddle_defense.dy)
                self.trace(
                    f"new x, y: {new_x_start}, {new_y_start}, dx, dy: {new_dx}, {new_dy}"
                )
                self.balltrack = BallTrack(
                    self.config,
                    new_x_start,
                    new_y_start,
                    new_dx,
                    new_dy,
                    time.time(),
                )
                continue

            # scoring happens
            self.logger.debug(
                f"Scoring happened({result.name}), "
                f"sleeping {self.config.t_delay_scoring} seconds"
            )
            await asyncio.sleep(self.config.t_delay_scoring)
            new_heading = BallTrack.Heading.opposite(self.balltrack.heading)
            new_dx, new_dy = get_random_dx_dy(self.config.v_ball, 20, new_heading)
            self.balltrack = BallTrack(
                self.config,
                self.config.x_ball_init,
                self.config.y_ball_init,
                new_dx,
                new_dy,
                time.time(),
            )

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

    async def wait_ball_travel(self) -> TurnResult:
        self.update_turns()

        # await until ball hits the other side
        await asyncio.sleep(self.balltrack.t_end - time.time())
        new_t = time.time()

        if new_t > self.t_end:
            self.logger.debug("time is up")
            self.time_over = True

        # only update defending paddle
        self.paddle_defense.update(new_t)
        if self.paddle_defense.hit(self.balltrack.y_impact):
            # success to defend, create reflection
            self.logger.debug(
                f"Player {self.paddle_defense.player.name} reflects the ball"
            )
            return TurnResult.DEFENDED
        else:
            # fail to defend, scoring, reset
            self.paddle_offense.score += 1
            self.logger.debug(f"Player {self.paddle_offense.player} scored")
            await self.emit_update_scores()
            self.logger.debug(
                f"Player {self.paddle_offense.player.name} scores to {self.paddle_offense.score}"
            )
            if self.paddle_offense.player == Player.A:
                return TurnResult.A_SCORED
            else:
                return TurnResult.B_SCORED

    async def emit_start(self) -> None:
        event = "start"
        data = {"t_event": self.t_start}
        # SIO: B>F start
        await sio.emit(event, data=data, namespace=self.namespace)
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

    async def emit_update_time_left(self, time_left: int) -> int:
        event = "update_time_left"
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
        for time_elapsed in range(int(self.config.t_limit) + 1):
            if not self.running:
                return

            time_left = int(self.config.t_limit) - time_elapsed
            await self.emit_update_time_left(time_left)

            next_emit_t = self.t_start + time_elapsed + 1
            await asyncio.sleep(next_emit_t - time.time())

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
        data = serialize_balltrack(self.balltrack)
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
        data = {"t_event": self.t_end, "winner": self.winner.name}
        # SIO: B>F ended
        await sio.emit(event, data=data, namespace=self.namespace)
        self.logger.debug(
            f"Emit event {event} data {data} to namespace {self.namespace}"
        )

    def __str__(self) -> str:
        return f"GameSession t_start={self.t_start}"

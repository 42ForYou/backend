import time
from typing import Dict

from GameConfig import GameConfig
from PaddleStatus import PaddleStatus, KeyInput, Player
from BallTrack import BallTrack


class GameSession:
    def __init__(
        self,
        width: float,
        height: float,
        epsilon: float,
        paddle_len: float,
        paddle_speed: float,
        ball_init_dx: float,
        ball_init_dy: float,
    ) -> None:
        self.config = GameConfig(width, height, paddle_speed, epsilon)
        self.paddles: Dict[Player, PaddleStatus] = {
            Player.A: PaddleStatus(self.config, paddle_len),  # LEFT
            Player.B: PaddleStatus(self.config, paddle_len),  # RIGHT
        }
        self.t_start = time.time()
        self.t_last_update = self.t_start
        self.balltrack = BallTrack(
            self.config, 0, 0, ball_init_dx, ball_init_dy, self.t_last_update
        )
        self.update_turns()

    def update_key(self, player: Player, key_input: KeyInput) -> None:
        self.paddles[player].update(key_input)

    def update_paddles(self, time_period: float) -> None:
        for _, paddle in self.paddles.items():
            new_y = paddle.y + paddle.dy * time_period

            if new_y > self.config.y_max:
                new_y = self.config.y_max
            if new_y < self.config.y_min:
                new_y = self.config.y_min

            paddle.y = new_y

    def update_turns(self) -> None:
        if self.balltrack.heading == BallTrack.Heading.LEFT:
            self.player_defense = Player.A
            self.player_offense = Player.B
        else:
            self.player_defense = Player.B
            self.player_offense = Player.A
        self.paddle_offense = self.paddles[self.player_offense]
        self.paddle_defense = self.paddles[self.player_defense]

    def update_ball(self, time_now: float) -> None:
        if time_now < self.balltrack.t_end:
            return

        if self.paddle_defense.hit(self.balltrack.y_impact):
            # create reflection
            new_x_start, new_y_start = self.balltrack.next_xy_start
            new_dx, new_dy = self.balltrack.next_dx_dy
            self.balltrack = BallTrack(
                self.config, new_x_start, new_y_start, new_dx, new_dy, time_now
            )
        else:
            # scoring, reset
            self.paddle_offense.score += 1
            new_dx, new_dy = self.balltrack.next_dx_dy
            self.balltrack = BallTrack(self.config, 0, 0, new_dx, new_dy, time_now)

        self.update_turns()

    def update(self) -> None:
        time_now = time.time()
        time_elapsed = time_now - self.t_last_update
        self.update_paddles(time_elapsed)
        self.update_ball(time_now)
        self.t_last_update = time_now

    def __str__(self) -> str:
        return f"GameSession t_start={self.t_start}, t_last_update={self.t_last_update}"

import time
from typing import Dict

from GameConfig import GameConfig
from PaddleStatus import PaddleStatus, KeyInput, Player
from BallTrack import BallTrack


# TODO: update print() statements to proper logging
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
        if self.config.flt_eq(ball_init_dx, 0.0):
            raise ValueError(f"GameSession got invalid dx {ball_init_dx}")
        self.paddles: Dict[Player, PaddleStatus] = {
            Player.A: PaddleStatus(self.config, paddle_len),  # LEFT
            Player.B: PaddleStatus(self.config, paddle_len),  # RIGHT
        }
        self.t_start = time.time()
        self.t_paddle_last = self.t_start
        self.balltrack = BallTrack(
            self.config, 0, 0, ball_init_dx, ball_init_dy, self.t_start
        )
        self.update_turns()
        print(f"{id(self)}: Created GameSession with {self.config}")
        print(f"{id(self)}: new {self.balltrack}")

    def update_key(self, player: Player, key_input: KeyInput) -> None:
        self.paddles[player].update(key_input)
        self.update_paddles(time.time())

    def update_paddles(self, time_now: float) -> None:
        time_elapsed = time_now - self.t_paddle_last

        for player, paddle in self.paddles.items():
            new_y = paddle.y + paddle.dy * time_elapsed

            if new_y > self.config.y_max:
                new_y = self.config.y_max
            if new_y < self.config.y_min:
                new_y = self.config.y_min

            paddle.y = new_y

            if paddle.dy != 0.0:
                print(f"{id(self)}: Player {player.name} paddle update to {paddle.y}")

        self.t_paddle_last = time_now

    def update_turns(self) -> None:
        if self.balltrack.heading == BallTrack.Heading.LEFT:
            self.player_defense = Player.A
            self.player_offense = Player.B
        else:
            self.player_defense = Player.B
            self.player_offense = Player.A
        self.paddle_offense = self.paddles[self.player_offense]
        self.paddle_defense = self.paddles[self.player_defense]
        print(
            f"{id(self)}: Attack: {self.player_offense.name} -> {self.player_defense.name}"
        )

    def update_ball(self, time_now: float) -> None:
        if time_now < self.balltrack.t_end:
            return

        print(f"{id(self)}: Ball hit the paddle side at {self.balltrack.t_end}")
        new_t = self.balltrack.t_end

        # TODO: resolve error from difference between actual impact time and paddle position
        if self.paddle_defense.hit(self.balltrack.y_impact):
            # create reflection
            print(f"{id(self)}: Player {self.player_defense.name} reflects the ball")
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
        else:
            # scoring, reset
            self.paddle_offense.score += 1
            print(
                f"{id(self)}: Player {self.player_offense.name} scores to {self.paddle_offense.score}"
            )
            new_dx, new_dy = self.balltrack.next_dx_dy
            self.balltrack = BallTrack(self.config, 0, 0, new_dx, new_dy, new_t)

        print(f"{id(self)}: new {self.balltrack}")
        self.update_turns()

    def update(self) -> None:
        time_now = time.time()
        self.update_paddles(time_now)
        self.update_ball(time_now)

    def __str__(self) -> str:
        return f"GameSession t_start={self.t_start}"

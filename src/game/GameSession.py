import time
from typing import List


class PaddleStatus:
    def __init__(self, len: float) -> None:
        self.y: float = 0.0
        self.dy: float = 0.0
        self.len = len


class BallTrackSegment:
    def __init__(
        self,
        x_start: float,
        y_start: float,
        x_end: float,
        y_end: float,
        dx: float,
        dy: float,
    ) -> None:
        self.x_start = x_start
        self.y_start = y_start
        self.x_end = x_end
        self.y_end = y_end
        self.dx = dx
        self.dy = dy


class BallTrack:
    def __init__(
        self, x_start: float, y_start: float, dx: float, dy: float, t_start: float
    ) -> None:
        self.x_start = x_start
        self.y_start = y_start
        self.dx = dx
        self.dy = dy
        # below: variables should be calculated with calculate_segments()
        self.is_calculated = False
        self.segments: List[BallTrackSegment] = []
        self.y_impact: float = 0.0
        self.t_impact: float = 0.0
        self.t_start = t_start
        self.t_end: float = 0.0
        self.calculate_segments()

    # Calculates the all ball track segments based on initial (x, y) and (dx, dy)
    # until the ball gets out of the game
    def calculate_segments() -> None:
        pass


class GameSession:
    def __init__(
        self,
        width: float,
        height: float,
        paddle_len: float,
        ball_init_dx: float,
        ball_init_dy: float,
    ) -> None:
        self.width = width
        self.height = height
        self.x_max = width / 2
        self.x_min = -width / 2
        self.y_max = height / 2
        self.y_min = -height / 2
        self.paddle_a = PaddleStatus(paddle_len)
        self.paddle_b = PaddleStatus(paddle_len)
        self.last_update_time = time.time()
        self.balltrack = BallTrack(
            0, 0, ball_init_dx, ball_init_dy, self.last_update_time
        )

    def update_paddles(self, time_period: float) -> None:
        for paddle in [self.paddle_a, self.paddle_b]:
            new_y = paddle.y + paddle.dy * time_period

            if new_y > self.height / 2:
                new_y = self.height / 2
            if new_y < -self.height / 2:
                new_y = -self.height / 2

    def update(self) -> None:
        pass

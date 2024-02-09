import time
import math
from typing import List, Tuple


class PaddleStatus:
    def __init__(self, len: float) -> None:
        self.y: float = 0.0
        self.dy: float = 0.0
        self.len = len

    def __str__(self) -> str:
        return f"Paddle(len={self.len}) at y={self.y}, dy={self.dy}"


class GameField:
    def __init__(
        self,
        width: float,
        height: float,
    ) -> None:
        self.width = width
        self.height = height
        self.x_max = width / 2
        self.x_min = -width / 2
        self.y_max = height / 2
        self.y_min = -height / 2


class BallTrackSegment:
    def __init__(
        self,
        field: GameField,
        x_start: float,
        y_start: float,
        x_end: float,
        y_end: float,
        dx: float,
        dy: float,
    ) -> None:
        self.field = field
        self.x_start = x_start
        self.y_start = y_start
        self.x_end = x_end
        self.y_end = y_end
        self.dx = dx
        self.dy = dy
        self.len = math.hypot(self.x_end - self.x_start, self.y_end - self.y_start)

    def __str__(self) -> str:
        return f"BallTrackSegment s=({self.x_start}, {self.y_start}) -> e=({self.x_end}, {self.y_end}), v=({self.dx}, {self.dy}), l={self.len}"

    @property
    def start_from_center(self) -> bool:
        return self.x_start == 0.0 and self.y_start == 0.0

    @property
    def is_inside_line(
        self,
        p_coord_constr: float,
        l_constr_min: float,
        l_constr_max: float,
        p_coord_range: float,
        l_range_min: float,
        l_range_max: float,
    ) -> bool:
        if not (p_coord_constr == l_constr_min or p_coord_constr == l_constr_max):
            return False
        if not (l_range_min <= p_coord_range <= l_range_max):
            return False
        return True

    @property
    def start_from_walls(self) -> bool:
        return self.is_inside_line(
            self.y_start,
            self.field.y_min,
            self.field.y_max,
            self.x_start,
            self.field.x_max,
            self.field.x_min,
        )

    @property
    def end_at_walls(self) -> bool:
        return self.is_inside_line(
            self.y_end,
            self.field.y_min,
            self.field.y_max,
            self.x_end,
            self.field.x_max,
            self.field.x_min,
        )

    @property
    def start_from_paddles(self) -> bool:
        return self.is_inside_line(
            self.x_start,
            self.field.x_min,
            self.field.x_max,
            self.y_start,
            self.field.y_max,
            self.field.y_min,
        )

    @property
    def end_at_paddles(self) -> bool:
        return self.is_inside_line(
            self.x_end,
            self.field.x_min,
            self.field.x_max,
            self.y_end,
            self.field.y_max,
            self.field.y_min,
        )

    @property
    def is_valid(self) -> bool:
        # start point can be either (0, 0) | on walls | on paddles
        if not (
            self.start_from_center or self.start_from_walls or self.start_from_paddles
        ):
            return False
        # end point can be either on walls | on paddles
        if not (self.end_at_walls or self.end_at_paddles):
            return False
        return True

    @property
    def next_dx_dy(self) -> Tuple[float, float]:
        if self.end_at_walls:  # vertical reflection
            return (self.dx, -self.dy)
        if self.end_at_paddles:  # horizontal reflection
            return (-self.dx, self.dy)
        raise ValueError("BallTrackSegment doesn't end at either walls or paddles")


def get_ball_track_segment_to_wall(
    field: GameField,
    x_start: float,
    y_start: float,
    dx: float,
    dy: float,
) -> BallTrackSegment:
    if dy == 0.0:
        raise ValueError("Ball cannot reach the walls (dy == 0.0)")

    y_wall = field.y_max
    # Calculate time to reach the wall (y = y_wall | -y_wall)
    t_impact = (y_wall - y_start) / dy
    # Calculate the x-coordinate of the impact point
    x_impact = x_start + dx * t_impact
    # Determine which wall is hit
    y_impact = y_wall if dy > 0 else -y_wall

    return BallTrackSegment(field, x_start, y_start, x_impact, y_impact, dx, dy)


def get_ball_track_segment_to_paddle(
    field: GameField,
    x_start: float,
    y_start: float,
    dx: float,
    dy: float,
) -> BallTrackSegment:
    if dx == 0.0:
        raise ValueError("Ball cannot reach the paddles (dx == 0.0)")

    x_paddle = field.x_max
    # Calculate time to reach the paddles (x = x_paddle | -x_paddle)
    t_impact = (x_paddle - x_start) / dx
    # Calculate the y-coordinate of the impact point
    y_impact = y_start + dy * t_impact
    # Determine which paddle is hit
    x_impact = x_paddle if dx > 0 else -x_paddle

    return BallTrackSegment(field, x_start, y_start, x_impact, y_impact, dx, dy)


class BallTrack:
    def __init__(
        self,
        field: GameField,
        x_start: float,
        y_start: float,
        dx_start: float,
        dy_start: float,
        t_start: float,
    ) -> None:
        self.field = field
        self.t_start = t_start
        # below: variables should be calculated with calculate_segments()
        self.segments: List[BallTrackSegment] = []
        self.y_impact: float = 0.0
        self.t_duration: float = 0.0
        self.t_end: float = 0.0
        self.calculate_segments(x_start, y_start, dx_start, dy_start)

    # Calculates the all ball track segments based on initial (x, y) and (dx, dy)
    # until the ball gets out of the game
    def calculate_segments(
        self, x_start: float, y_start: float, dx: float, dy: float
    ) -> None:
        v = math.hypot(dx, dy)

        while True:
            next_track = get_ball_track_segment_to_wall(
                self.field, x_start, y_start, dx, dy
            )
            if next_track.is_valid:
                self.segments.append(next_track)
                x_start = next_track.x_end
                y_start = next_track.y_end
                dx, dy = next_track.next_dx_dy
                continue

            # ball doesn't hit the wall, thus must hit paddle side
            next_track = get_ball_track_segment_to_paddle(
                self.field, x_start, y_start, dx, dy
            )
            if next_track.is_valid:
                self.segments.append(next_track)
                break

            # ball doesn't hit walls neither paddles?
            raise ValueError("Error while calculating ball's movement")

        self.y_impact = self.segments[-1].y_end
        len_total = sum([seg.len for seg in self.segments])
        self.t_duration = len_total / v  # v * t = d, t = d / v
        self.t_end = self.t_start + self.t_duration

    def __str__(self) -> str:
        pts = [f"({seg.x_start}, {seg.y_start})" for seg in self.segments]
        pts.append(f"({self.segments[-1].x_end}, {self.segments[-1].y_end})")
        pts_str = " > ".join(pts)
        return f"BallTrack {self.heading}, v={self.v}, {pts_str}"


class GameSession:
    def __init__(
        self,
        width: float,
        height: float,
        paddle_len: float,
        ball_init_dx: float,
        ball_init_dy: float,
    ) -> None:
        self.field = GameField(width, height)
        self.paddle_a = PaddleStatus(paddle_len)
        self.paddle_b = PaddleStatus(paddle_len)
        self.last_update_time = time.time()
        self.balltrack = BallTrack(
            self.field, 0, 0, ball_init_dx, ball_init_dy, self.last_update_time
        )

    def update_paddles(self, time_period: float) -> None:
        for paddle in [self.paddle_a, self.paddle_b]:
            new_y = paddle.y + paddle.dy * time_period

            if new_y > self.field.y_max:
                new_y = self.field.y_max
            if new_y < self.field.y_min:
                new_y = self.field.y_min

            paddle.y = new_y

    def update(self) -> None:
        pass

    def __str__(self) -> str:
        return f"GameSession t_start={self.t_start}, t_last_update={self.t_last_update}"

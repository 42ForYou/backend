import math
from typing import Tuple

from GameConfig import GameConfig


class BallTrackSegment:
    def __init__(
        self,
        config: GameConfig,
        x_start: float,
        y_start: float,
        x_end: float,
        y_end: float,
        dx: float,
        dy: float,
    ) -> None:
        self.config = config
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
        return self.config.flt_eq(self.x_start, 0.0) and self.config.flt_eq(
            self.y_start, 0.0
        )

    def is_inside_line(
        self,
        p_coord_constr: float,
        l_constr_min: float,
        l_constr_max: float,
        p_coord_range: float,
        l_range_min: float,
        l_range_max: float,
    ) -> bool:
        if not (
            self.config.flt_eq(p_coord_constr, l_constr_min)
            or self.config.flt_eq(p_coord_constr, l_constr_max)
        ):
            return False
        if not (l_range_min <= p_coord_range <= l_range_max):
            return False
        return True

    @property
    def start_from_walls(self) -> bool:
        return self.is_inside_line(
            self.y_start,
            self.config.y_min,
            self.config.y_max,
            self.x_start,
            self.config.x_max,
            self.config.x_min,
        )

    @property
    def end_at_walls(self) -> bool:
        return self.is_inside_line(
            self.y_end,
            self.config.y_min,
            self.config.y_max,
            self.x_end,
            self.config.x_max,
            self.config.x_min,
        )

    @property
    def start_from_paddles(self) -> bool:
        return self.is_inside_line(
            self.x_start,
            self.config.x_min,
            self.config.x_max,
            self.y_start,
            self.config.y_max,
            self.config.y_min,
        )

    @property
    def end_at_paddles(self) -> bool:
        return self.is_inside_line(
            self.x_end,
            self.config.x_min,
            self.config.x_max,
            self.y_end,
            self.config.y_max,
            self.config.y_min,
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

    @property
    def next_xy_start(self) -> Tuple[float, float]:
        return (self.x_end, self.y_end)


def get_ball_track_segment_to_wall(
    config: GameConfig,
    x_start: float,
    y_start: float,
    dx: float,
    dy: float,
) -> BallTrackSegment:
    if config.flt_eq(dy, 0.0):
        raise ValueError("Ball cannot reach the walls (dy == 0.0)")

    y_wall = config.y_max
    # Calculate time to reach the wall (y = y_wall | -y_wall)
    t_impact = (y_wall - y_start) / dy
    # Calculate the x-coordinate of the impact point
    x_impact = x_start + dx * t_impact
    # Determine which wall is hit
    y_impact = y_wall if dy > 0 else -y_wall

    return BallTrackSegment(config, x_start, y_start, x_impact, y_impact, dx, dy)


def get_ball_track_segment_to_paddle(
    config: GameConfig,
    x_start: float,
    y_start: float,
    dx: float,
    dy: float,
) -> BallTrackSegment:
    if config.flt_eq(dx, 0.0):
        raise ValueError("Ball cannot reach the paddles (dx == 0.0)")

    x_paddle = config.x_max
    # Calculate time to reach the paddles (x = x_paddle | -x_paddle)
    t_impact = (x_paddle - x_start) / dx
    # Calculate the y-coordinate of the impact point
    y_impact = y_start + dy * t_impact
    # Determine which paddle is hit
    x_impact = x_paddle if dx > 0 else -x_paddle

    return BallTrackSegment(config, x_start, y_start, x_impact, y_impact, dx, dy)

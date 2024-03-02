import math
from typing import Tuple
from enum import Enum

from livegame.SubGameConfig import SubGameConfig


class PointCategory(Enum):
    INVALID = 0
    CENTER = 1
    WALL_TOP = 2
    WALL_BOTTOM = 3
    PADDLE_LEFT = 4
    PADDLE_RIGHT = 5


class BallTrackSegment:

    def __init__(
        self,
        config: SubGameConfig,
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
        self.p_start = PointCategory.INVALID
        self.p_end = PointCategory.INVALID
        self.is_valid = False
        self.calculate_validity()

    def __str__(self) -> str:
        result = f"{self.__class__.__name__} "
        result += f"s=({self.x_start}, {self.y_start}) [{self.p_start.name}] -> "
        result += f"e=({self.x_end}, {self.y_end}) [{self.p_end.name}], "
        result += f"v=({self.dx}, {self.dy}), l={self.len}"
        return result

    @property
    def start_from_center(self) -> bool:
        result = self.config.flt_eq(self.x_start, 0.0) and self.config.flt_eq(
            self.y_start, 0.0
        )
        if result:
            self.p_start = PointCategory.CENTER
        return result

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
        result = self.is_inside_line(
            self.y_start,
            self.config.y_min,
            self.config.y_max,
            self.x_start,
            self.config.x_min,
            self.config.x_max,
        )
        if result:
            if self.y_start > 0:
                self.p_start = PointCategory.WALL_TOP
            else:
                self.p_start = PointCategory.WALL_BOTTOM
        return result

    @property
    def end_at_walls(self) -> bool:
        result = self.is_inside_line(
            self.y_end,
            self.config.y_min,
            self.config.y_max,
            self.x_end,
            self.config.x_min,
            self.config.x_max,
        )
        if result:
            if self.y_end > 0:
                self.p_end = PointCategory.WALL_TOP
            else:
                self.p_end = PointCategory.WALL_BOTTOM
        return result

    @property
    def start_from_paddles(self) -> bool:
        result = self.is_inside_line(
            self.x_start,
            self.config.x_min,
            self.config.x_max,
            self.y_start,
            self.config.y_min,
            self.config.y_max,
        )
        if result:
            if self.x_start > 0:
                self.p_start = PointCategory.PADDLE_RIGHT
            else:
                self.p_start = PointCategory.PADDLE_LEFT
        return result

    @property
    def end_at_paddles(self) -> bool:
        result = self.is_inside_line(
            self.x_end,
            self.config.x_min,
            self.config.x_max,
            self.y_end,
            self.config.y_min,
            self.config.y_max,
        )
        if result:
            if self.x_end > 0:
                self.p_end = PointCategory.PADDLE_RIGHT
            else:
                self.p_end = PointCategory.PADDLE_LEFT
        return result

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

    def calculate_validity(self) -> None:
        self.is_valid = False
        # start point can be either (0, 0) | on walls | on paddles
        if not (
            self.start_from_center or self.start_from_walls or self.start_from_paddles
        ):
            return
        # end point can be either on walls | on paddles
        if not (self.end_at_walls or self.end_at_paddles):
            return

        if self.p_start == PointCategory.INVALID or self.p_end == PointCategory.INVALID:
            raise ValueError("p_start or p_end is invalid")
        self.is_valid = True


def get_ball_track_segment_to_wall(
    config: SubGameConfig,
    x_start: float,
    y_start: float,
    dx: float,
    dy: float,
) -> BallTrackSegment:
    if config.flt_eq(dy, 0.0):
        raise ValueError("Ball cannot reach the walls (dy == 0.0)")

    y_impact = config.y_max if dy > 0 else config.y_min
    # Calculate time to reach the wall (y = y_impact | -y_impact)
    t_impact = (y_impact - y_start) / dy
    # Calculate the x-coordinate of the impact point
    x_impact = x_start + dx * t_impact
    # Determine which wall is hit

    return BallTrackSegment(config, x_start, y_start, x_impact, y_impact, dx, dy)


def get_ball_track_segment_to_paddle(
    config: SubGameConfig,
    x_start: float,
    y_start: float,
    dx: float,
    dy: float,
) -> BallTrackSegment:
    if config.flt_eq(dx, 0.0):
        raise ValueError("Ball cannot reach the paddles (dx == 0.0)")

    x_impact = config.x_max if dx > 0 else config.x_min
    # Calculate time to reach the paddles (x = x_impact | -x_impact)
    t_impact = (x_impact - x_start) / dx
    # Calculate the y-coordinate of the impact point
    y_impact = y_start + dy * t_impact
    # Determine which paddle is hit

    return BallTrackSegment(config, x_start, y_start, x_impact, y_impact, dx, dy)

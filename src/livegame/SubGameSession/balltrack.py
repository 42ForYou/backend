import math
import random
import logging
from typing import List, Tuple
from enum import Enum

from pong.settings import LOGLEVEL_TRACE_ENABLE
from ..subgame_config import SubGameConfig
from .balltrack_segment import (
    BallTrackSegment,
    get_ball_track_segment_to_wall,
    get_ball_track_segment_to_paddle,
)


class BallTrack:
    class Heading(Enum):
        LEFT = 1
        RIGHT = 2

        @staticmethod
        def opposite(heading):
            opposite_map = {
                BallTrack.Heading.LEFT: BallTrack.Heading.RIGHT,
                BallTrack.Heading.RIGHT: BallTrack.Heading.LEFT,
            }
            return opposite_map[heading]

    def __init__(
        self,
        config: SubGameConfig,
        x_start: float,
        y_start: float,
        dx_start: float,
        dy_start: float,
        t_start: float,
    ) -> None:
        if config.flt_eq(dx_start, 0.0):
            raise ValueError("Cannot construct BallTrack because dx is 0.0")
        self.config = config
        self.logger = logging.getLogger(f"{__package__}.{self.__class__.__name__}")
        self.t_start = t_start
        self.v = math.hypot(dx_start, dy_start)
        self.heading = (
            BallTrack.Heading.LEFT if dx_start < 0 else BallTrack.Heading.RIGHT
        )
        # below: variables should be calculated with calculate_segments()
        self.segments: List[BallTrackSegment] = []
        self.y_impact: float = 0.0
        self.t_duration: float = 0.0
        self.t_end: float = 0.0
        self.calculate_segments(x_start, y_start, dx_start, dy_start)

    def trace(self, msg: str) -> None:
        if LOGLEVEL_TRACE_ENABLE != "0":
            self.logger.debug(f"[TRACE] {msg}")

    # Calculates the all ball track segments based on initial (x, y) and (dx, dy)
    # until the ball gets out of the game
    def calculate_segments(
        self, x_start: float, y_start: float, dx: float, dy: float
    ) -> None:
        while True:
            self.trace(f"calculate_segments loop start")
            self.trace(f"call get_ball_track_segment_to_wall")
            next_track = get_ball_track_segment_to_wall(
                self.config, x_start, y_start, dx, dy
            )
            if next_track.is_valid:
                self.trace(f"next track is valid")
                self.segments.append(next_track)
                x_start = next_track.x_end
                y_start = next_track.y_end
                dx, dy = next_track.next_dx_dy
                self.trace(f"x_start {x_start} y_start {y_start} dx {dx} dy {dy}")
                self.trace(f"continue...")
                continue

            # ball doesn't hit the wall, thus must hit paddle side
            next_track = get_ball_track_segment_to_paddle(
                self.config, x_start, y_start, dx, dy
            )
            self.trace(f"call get_ball_track_segment_to_paddle")
            if next_track.is_valid:
                self.trace(f"next track is valid")
                self.segments.append(next_track)
                self.trace("break")
                break

            # ball doesn't hit walls neither paddles?
            raise ValueError("Error while calculating ball's movement")

        self.y_impact = self.segments[-1].y_end
        len_total = sum([seg.len for seg in self.segments])
        self.t_duration = len_total / self.v  # v * t = d, t = d / v
        self.t_end = self.t_start + self.t_duration
        self.trace(
            f"self.y_impact {self.y_impact} len_total {len_total} self.t_end {self.t_end}"
        )

    def next_dx_dy(self, paddle_dy: float) -> Tuple[float, float]:
        new_dx, new_dy = self.segments[-1].next_dx_dy
        new_dy += paddle_dy * self.config.u_paddle
        return new_dx, new_dy

    @property
    def next_xy_start(self) -> Tuple[float, float]:
        return self.segments[-1].next_xy_start

    def __str__(self) -> str:
        pts = [f"({seg.x_start}, {seg.y_start})" for seg in self.segments]
        pts.append(f"({self.segments[-1].x_end}, {self.segments[-1].y_end})")
        pts_str = " > ".join(pts)
        return f"BallTrack {self.heading.name}, dt={self.t_duration}, t={self.t_start}...{self.t_end}, v={self.v}, {pts_str}"


def get_random_dx_dy(
    v: float, excluded_angle_scope: float, heading=None
) -> Tuple[float, float]:
    if heading is None:
        heading = random.choice([BallTrack.Heading.LEFT, BallTrack.Heading.RIGHT])

    # Convert excluded_angle_scope from degrees to radians
    exc = math.radians(excluded_angle_scope)

    # Function to check if an angle is within the excluded scope near the x or y axes
    def is_excluded(angle):
        # Check proximity to the x-axis
        if (angle < exc or angle > math.pi - exc) or (
            angle > math.pi + exc and angle < 2 * math.pi - exc
        ):
            return True
        # Check proximity to the y-axis
        if (angle > math.pi / 2 - exc and angle < math.pi / 2 + exc) or (
            angle > 3 * math.pi / 2 - exc and angle < 3 * math.pi / 2 + exc
        ):
            return True
        return False

    while True:
        angle = random.uniform(0, 2 * math.pi)
        if not is_excluded(angle):
            break

    dx = v * math.cos(angle)
    dy = v * math.sin(angle)

    if (heading == BallTrack.Heading.LEFT and dx >= 0) or (
        heading == BallTrack.Heading.RIGHT and dx <= 0
    ):
        dx = -dx

    return dx, dy

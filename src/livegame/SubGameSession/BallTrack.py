import math
from typing import List, Tuple
from enum import Enum

from livegame.SubGameConfig import SubGameConfig
from livegame.SubGameSession.BallTrackSegment import (
    BallTrackSegment,
    get_ball_track_segment_to_wall,
    get_ball_track_segment_to_paddle,
)


class BallTrack:
    class Heading(Enum):
        LEFT = 1
        RIGHT = 2

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

    # Calculates the all ball track segments based on initial (x, y) and (dx, dy)
    # until the ball gets out of the game
    def calculate_segments(
        self, x_start: float, y_start: float, dx: float, dy: float
    ) -> None:
        while True:
            next_track = get_ball_track_segment_to_wall(
                self.config, x_start, y_start, dx, dy
            )
            if next_track.is_valid:
                self.segments.append(next_track)
                x_start = next_track.x_end
                y_start = next_track.y_end
                dx, dy = next_track.next_dx_dy
                continue

            # ball doesn't hit the wall, thus must hit paddle side
            next_track = get_ball_track_segment_to_paddle(
                self.config, x_start, y_start, dx, dy
            )
            if next_track.is_valid:
                self.segments.append(next_track)
                break

            # ball doesn't hit walls neither paddles?
            raise ValueError("Error while calculating ball's movement")

        self.y_impact = self.segments[-1].y_end
        len_total = sum(seg.len for seg in self.segments)
        self.t_duration = len_total / self.v  # v * t = d, t = d / v
        self.t_end = self.t_start + self.t_duration

    @property
    def next_dx_dy(self) -> Tuple[float, float]:
        return self.segments[-1].next_dx_dy

    @property
    def next_xy_start(self) -> Tuple[float, float]:
        return self.segments[-1].next_xy_start

    def __str__(self) -> str:
        pts = [f"({seg.x_start}, {seg.y_start})" for seg in self.segments]
        pts.append(f"({self.segments[-1].x_end}, {self.segments[-1].y_end})")
        pts_str = " > ".join(pts)
        return (
            f"BallTrack {self.heading.name}, "
            f"dt={self.t_duration}, t={self.t_start}...{self.t_end}, "
            f"v={self.v}, {pts_str}"
        )

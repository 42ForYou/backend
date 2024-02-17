from livegame.SubGameSession.BallTrack import BallTrack
from livegame.SubGameSession.BallTrackSegment import BallTrackSegment


def serialize_balltracksegment(seg: BallTrackSegment):
    return {
        "x_s": seg.x_start,
        "y_s": seg.x_start,
        "x_e": seg.x_end,
        "y_e": seg.y_end,
        "dx": seg.dx,
        "dy": seg.dy,
    }


def serialize_balltrack(balltrack: BallTrack):
    return [serialize_balltracksegment(seg) for seg in balltrack.segments]

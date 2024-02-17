from livegame.SubGameSession.BallTrack import BallTrack
from livegame.SubGameSession.BallTrackSegment import BallTrackSegment
from livegame.SubGameConfig import SubGameConfig


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


def serialize_subgame_config(config: SubGameConfig):
    return {
        "match_point": config.match_point,
        "player_a_init_point": config.player_a_init_point,
        "player_b_init_point": config.player_b_init_point,
        "time_limit": config.t_limit,
        "x_max": config.x_max,
        "y_max": config.y_max,
        "x_min": config.x_min,
        "y_min": config.y_min,
        "v_paddle": config.v_paddle,
        "len_paddle": config.l_paddle,
        "v_ball": config.v_ball,
    }

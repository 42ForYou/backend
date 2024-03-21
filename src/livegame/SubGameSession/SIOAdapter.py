from livegame.SubGameSession.BallTrack import BallTrack
from livegame.SubGameSession.BallTrackSegment import BallTrackSegment
from livegame.SubGameConfig import SubGameConfig
from livegame.precision_config import round_coord, round_speed, round_time


def serialize_balltracksegment(seg: BallTrackSegment):
    return {
        "x_s": round_coord(seg.x_start),
        "y_s": round_coord(seg.y_start),
        "x_e": round_coord(seg.x_end),
        "y_e": round_coord(seg.y_end),
        "dx": round_speed(seg.dx),
        "dy": round_speed(seg.dy),
    }


def serialize_balltrack(balltrack: BallTrack):
    return {
        "t_event": round_time(balltrack.t_start),
        "t_end": round_time(balltrack.t_end),
        "heading": balltrack.heading.name,
        "velocity": round_speed(balltrack.v),
        "segments": [serialize_balltracksegment(seg) for seg in balltrack.segments],
    }


def serialize_subgame_config(config: SubGameConfig):
    return {
        "match_point": config.match_point,  # 승리를 위해 필요한 득점
        "player_a_init_point": config.player_a_init_point,  # 플레이어 A의 초기 점수 (아마도 0)
        "player_b_init_point": config.player_b_init_point,  # 플레이어 B의 초기 점수 (아마도 0)
        "time_limit": round_time(config.t_limit),  # 경기 시간 제한
        "x_max": round_coord(config.x_max),  # 현재 게임의 최대/최소 x/y 좌표값
        "y_max": round_coord(config.y_max),  # 현재 게임의 최대/최소 x/y 좌표값
        "x_min": round_coord(config.x_min),  # 현재 게임의 최대/최소 x/y 좌표값
        "y_min": round_coord(config.y_min),  # 현재 게임의 최대/최소 x/y 좌표값
        "x_init_ball": round_coord(config.x_ball_init),  # 공의 최초 x 좌표
        "y_init_ball": round_coord(config.y_ball_init),  # 공의 최초 y 좌표
        "y_init_paddle": round_coord(config.y_paddle_init),  # 패들의 최초 y 좌표
        "v_paddle": round_speed(config.v_paddle),  # 패들의 속력
        # 패들의 길이 (마진 포함)
        "len_paddle": round_coord(config.l_paddle + config.l_paddle_m),
        "u_paddle": round_speed(config.u_paddle),  # 패들의 마찰계수
        "v_ball": round_speed(config.v_ball),  # 공의 초기 속력
        # 각 "강" 시작시, /gameroom @update_tournament 부터 /subgame @start 까지 딜레이 시간
        "delay_rank_start": round_time(config.t_delay_rank_start),
        # 각 서브게임 시작시, /subgame @start 부터 게임 시뮬레이션 개시까지 딜레이 시간
        "delay_subgame_start": round_time(config.t_delay_subgame_start),
        # 한 플레이어가 득점 시 다음 턴 시작까지 딜레이 시간
        "delay_scoring": round_time(config.t_delay_scoring),
        # 각 "강" 내부의 서브게임이 모두 끝난 후 다음 "강" 시작 /gameroom @update_tournament까지 딜레이 시간
        "delay_rank_end": round_time(config.t_delay_rank_end),
    }

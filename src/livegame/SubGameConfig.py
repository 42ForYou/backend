import math


class SubGameConfig:
    def __init__(
        self,
        width: float,
        height: float,
        match_point: int,
        player_a_init_point: int,
        player_b_init_point: int,
        paddle_len: float,
        paddle_speed: float,
        epsilon: float,  # expected floating point error
        ball_init_x: float,
        ball_init_y: float,
        ball_speed: float,
        time_limit: float,
        time_before_start: float,
    ) -> None:
        self.width = width
        self.height = height
        self.match_point = match_point
        self.player_a_init_point = player_a_init_point
        self.player_b_init_point = player_b_init_point
        self.x_max = width / 2
        self.x_min = -width / 2
        self.y_max = height / 2
        self.y_min = -height / 2
        self.l_paddle = paddle_len
        self.v_paddle = paddle_speed
        self.e = abs(epsilon)
        self.x_ball_init = ball_init_x
        self.y_ball_init = ball_init_y
        self.v_ball = ball_speed
        self.t_limit = time_limit
        self.time_before_start = time_before_start

    def __str__(self) -> str:
        return f"SubGameConfig {self.width} * {self.height} (e={self.e}), v_paddle={self.v_paddle}, l_paddle={self.l_paddle}, {self.x_min} <= x <= {self.x_max}, {self.y_min} <= y <= {self.y_max}"

    # Checks whether two numbers can be considered equal (difference is within epsilon)
    def flt_eq(self, a: float, b: float) -> bool:
        return math.isclose(a, b, abs_tol=self.e)


# TODO: move setting value to somewhere else
def get_default_subgame_config() -> SubGameConfig:
    return SubGameConfig(
        width=800,
        height=600,
        match_point=10,
        player_a_init_point=0,
        player_b_init_point=0,
        paddle_len=50,
        paddle_speed=100,
        epsilon=1,
        ball_init_x=0,
        ball_init_y=0,
        ball_speed=200,
        time_limit=60,
        time_before_start=5.0,
    )

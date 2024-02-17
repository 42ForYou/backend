import math


class SubGameConfig:
    def __init__(
        self,
        width: float,
        height: float,
        match_point: float,
        paddle_len: float,
        paddle_speed: float,
        epsilon: float,  # expected floating point error
        dx_ball: float,
        dy_ball: float,
        time_limit: float,
    ) -> None:
        self.width = width
        self.height = height
        self.match_point = match_point
        self.x_max = width / 2
        self.x_min = -width / 2
        self.y_max = height / 2
        self.y_min = -height / 2
        self.l_paddle = paddle_len
        self.v_paddle = paddle_speed
        self.e = abs(epsilon)
        self.dx_ball = dx_ball
        self.dy_ball = dy_ball
        self.v_ball = math.hypot(dx_ball, dy_ball)
        self.t_limit = time_limit

    def __str__(self) -> str:
        return f"SubGameConfig {self.width} * {self.height} (e={self.e}), v_paddle={self.v_paddle}, l_paddle={self.l_paddle}, {self.x_min} <= x <= {self.x_max}, {self.y_min} <= y <= {self.y_max}"

    # Checks whether two numbers can be considered equal (difference is within epsilon)
    def flt_eq(self, a: float, b: float) -> bool:
        return math.isclose(a, b, abs_tol=self.e)

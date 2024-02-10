class GameConfig:
    def __init__(
        self,
        width: float,
        height: float,
        v_paddle: float,
    ) -> None:
        self.width = width
        self.height = height
        self.x_max = width / 2
        self.x_min = -width / 2
        self.y_max = height / 2
        self.y_min = -height / 2
        self.v_paddle = v_paddle

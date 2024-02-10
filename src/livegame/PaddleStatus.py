class PaddleStatus:
    def __init__(self, len: float) -> None:
        self.y: float = 0.0
        self.dy: float = 0.0
        self.len = len
        self.score = 0

    def hit(self, y_ball: float) -> bool:
        return self.y - self.len / 2 <= y_ball <= self.y + self.len

    def __str__(self) -> str:
        return f"Paddle(len={self.len}) at y={self.y}, dy={self.dy}"

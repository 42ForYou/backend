from dataclasses import dataclass
from enum import Enum
from typing import Dict

from GameConfig import GameConfig


class Player(Enum):
    A = 0  # LEFT
    B = 1  # RIGHT


@dataclass
class KeyInput:
    class Key(Enum):
        UP = 0
        DOWN = 1

    class Action(Enum):
        PRESS = 0
        RELEASE = 1

    key: Key
    action: Action


class PaddleStatus:
    def __init__(self, config: GameConfig, len: float) -> None:
        self.config = config
        self.y: float = 0.0
        self.dy: float = 0.0
        self.len = len
        self.score = 0
        self.key_pressed: Dict[KeyInput.Key, bool] = {
            KeyInput.Key.UP: False,
            KeyInput.Key.DOWN: False,
        }

    def update(self, key_input: KeyInput) -> None:
        if key_input.action == KeyInput.Action.PRESS:
            self.key_pressed[key_input.key] = True

            # When pressing, update dy simply according to pressed key
            if key_input.key == KeyInput.Key.UP:
                self.dy = self.config.v_paddle
            elif key_input.key == KeyInput.Key.DOWN:
                self.dy = -self.config.v_paddle

        elif key_input.action == KeyInput.Action.RELEASE:
            self.key_pressed[key_input.key] = False

            # When releasing, if other key remains being pressed, update dy according to remaining key
            # if no key is pressed, update dy to 0
            if key_input.key == KeyInput.Key.UP:
                if self.key_pressed[KeyInput.Key.DOWN]:
                    self.dy = -self.config.v_paddle
                else:
                    self.dy = 0
            elif key_input.key == KeyInput.Key.DOWN:
                if self.key_pressed[KeyInput.Key.UP]:
                    self.dy = self.config.v_paddle
                else:
                    self.dy = 0

        else:
            raise ValueError(f"Invalid KeyInput Action: {key_input}")

    def hit(self, y_ball: float) -> bool:
        return self.y - self.len / 2 <= y_ball <= self.y + self.len

    def __str__(self) -> str:
        return f"Paddle(len={self.len}) at y={self.y}, dy={self.dy}"
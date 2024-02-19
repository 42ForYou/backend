from dataclasses import dataclass
from enum import Enum
from typing import Dict

from livegame.SubGameConfig import SubGameConfig


class Player(Enum):
    NOBODY = 0
    A = 1  # LEFT
    B = 2  # RIGHT


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
    def __init__(self, config: SubGameConfig, player: Player, time_now: float) -> None:
        self.config = config
        self.player = player
        self.y: float = 0.0
        self.dy: float = 0.0
        self.score = 0
        self.key_pressed: Dict[KeyInput.Key, bool] = {
            KeyInput.Key.UP: False,
            KeyInput.Key.DOWN: False,
        }
        self.t_last_updated = time_now

    def update(self, time_now: float) -> None:
        time_elapsed = time_now - self.t_last_updated

        new_y = self.y + self.dy * time_elapsed
        if new_y > self.config.y_max:
            new_y = self.config.y_max
        if new_y < self.config.y_min:
            new_y = self.config.y_min
        self.y = new_y

        self.t_last_updated = time_now

    def update_key(self, key_input: KeyInput) -> None:
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
        return (
            self.y - self.config.l_paddle / 2 <= y_ball <= self.y + self.config.l_paddle
        )

    def __str__(self) -> str:
        return f"Paddle(l={self.config.l_paddle}) at y={self.y}, dy={self.dy}"

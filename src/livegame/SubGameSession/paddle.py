import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Union

from pong.settings import LOGLEVEL_TRACE_ENABLE
from ..precision_config import round_time, round_coord, round_speed
from ..subgame_config import SubGameConfig


class Player(Enum):
    NOBODY = 0
    A = 1  # LEFT
    B = 2  # RIGHT


class PaddleAckStatus(Enum):
    CREATED = 0
    STARTED = 1
    ENDED = 2


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


class Paddle:
    def __init__(self, config: SubGameConfig, player: Player, time_now: float) -> None:
        self.config = config
        self.logger = logging.getLogger(
            f"{__package__}.{self.__class__.__name__}.{player.name}"
        )
        self.player = player
        self.y = self.config.y_paddle_init
        self.y_max = self.config.y_max - self.config.l_paddle / 2
        self.y_min = self.config.y_min + self.config.l_paddle / 2
        self.dy: float = 0.0
        self.score = 0
        self.key_pressed: Dict[KeyInput.Key, bool] = {
            KeyInput.Key.UP: False,
            KeyInput.Key.DOWN: False,
        }
        self.t_last_updated = time_now
        self.last_key_input: Union[None, KeyInput] = None
        self.ack_status = PaddleAckStatus.CREATED

    def trace(self, msg: str) -> None:
        if LOGLEVEL_TRACE_ENABLE != "0":
            self.logger.debug(f"[TRACE] {msg}")

    def update(self, time_now: float) -> None:
        time_elapsed = time_now - self.t_last_updated
        self.trace(f"{time_elapsed} seconds passed")

        new_y = self.y + self.dy * time_elapsed
        self.trace(f"new_y: {new_y}")
        if new_y > self.y_max:
            new_y = self.y_max
            self.trace(f"new_y clipped to max {new_y}")
        if new_y < self.y_min:
            new_y = self.y_min
            self.trace(f"new_y clipped to min {new_y}")
        self.y = new_y

        self.t_last_updated = time_now
        self.trace(f"t_last_updated {self.t_last_updated}")

    def update_key(self, key_input: KeyInput, time_now: float) -> bool:
        if self.last_key_input == key_input:
            self.trace(f"ignore key input same with last input: {key_input}")
            return False

        self.trace(f"update_key {key_input}")
        self.last_key_input = key_input
        self.update(time_now)

        if key_input.action == KeyInput.Action.PRESS:
            self.key_pressed[key_input.key] = True

            # When pressing, update dy simply according to pressed key
            if key_input.key == KeyInput.Key.UP:
                self.dy = self.config.v_paddle
            elif key_input.key == KeyInput.Key.DOWN:
                self.dy = -self.config.v_paddle

        elif key_input.action == KeyInput.Action.RELEASE:
            self.key_pressed[key_input.key] = False

            # When releasing, if other key remains being pressed,
            # update dy according to remaining key
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

        self.trace(f"self.dy {self.dy}")
        return True

    def hit(self, y_ball: float) -> bool:
        result = (
            self.y - self.config.l_paddle / 2
            <= y_ball
            <= self.y + self.config.l_paddle / 2
        )
        self.trace(f"y_ball {y_ball} => hit: {result}")
        return result

    def to_dict(self) -> dict:
        return {
            "t_event": round_time(self.t_last_updated),
            "player": self.player.name,
            "y": round_coord(self.y),
            "dy": round_speed(self.dy),
        }

    def __str__(self) -> str:
        return f"Paddle(l={self.config.l_paddle}) at y={self.y}, dy={self.dy}"

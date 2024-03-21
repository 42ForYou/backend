import time
import os


prc_time = int(os.environ.get("PRECISION_TIME", "3"))
prc_coord = int(os.environ.get("PRECISION_COORD", "1"))
prc_speed = int(os.environ.get("PRECISION_SPEED", "2"))


def get_time() -> float:
    return round(time.time(), prc_time)


def round_time(val: float) -> float:
    if isinstance(val, float):
        return val
    return round(val, prc_time)


def round_coord(val: float) -> float:
    if isinstance(val, float):
        return val
    return round(val, prc_coord)


def round_speed(val: float) -> float:
    if isinstance(val, float):
        return val
    return round(val, prc_speed)

from pong.asgi import sio
from GameSession import GameSession


class ValueUpdateManager:
    def __init__(self) -> None:
        self.initialized: bool = False

    # Update internal value to given one and returns True if given value is new.
    def update(self, new_val) -> bool:
        if not self.initialized:
            self.val = new_val
            self.initialized = True
            return True

        is_new = self.val != new_val
        self.val = new_val
        return is_new


class GameSessionSIOAdapter:
    def __init__(
        self, session: GameSession, room_id: int, rank: int, idx_in_rank: int
    ) -> None:
        self.session = session
        self.time_left = ValueUpdateManager()
        self.room_id = room_id
        self.rank = rank
        self.idx_in_rank = idx_in_rank

    def update(self) -> None:
        self.session.update()

        if self.time_left.update(self.session.get_time_left()):
            # update_time_left
            pass

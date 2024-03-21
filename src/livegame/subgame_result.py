from typing import Union

from accounts.models import UserDataCache
from livegame.precision_config import round_time
from livegame.SubGameSession.subgame_session import SubGameSession


class SubGameResult:
    def __init__(self, session: Union[SubGameSession, None]) -> None:
        self.session = session
        self.sid_a: Union[str, None] = None
        self.sid_b: Union[str, None] = None
        self.user_data_a: Union[UserDataCache, None] = None
        self.user_data_b: Union[UserDataCache, None] = None
        self.winner: Union[str, None] = None
        self.t_start: Union[float, None] = None
        self.t_end: Union[float, None] = None

    def to_dict(self) -> dict:
        result = {
            "player_a": None if self.sid_a is None else self.user_data_a.to_dict(),
            "player_b": None if self.sid_b is None else self.user_data_b.to_dict(),
            "winner": self.winner,
            "t_start": round_time(self.t_start),
            "t_end": round_time(self.t_end),
        }

        return result

    def get_sid_of_winner(self) -> str:
        if not self.winner:
            raise ValueError("Winner is not yet determined")

        if self.winner == "A":
            return self.sid_a
        if self.winner == "B":
            return self.sid_b
        raise ValueError(f"Invalid winner value: {self.winner}")

    def get_user_data_of_winner(self) -> UserDataCache:
        if not self.winner:
            raise ValueError("Winner is not yet determined")

        if self.winner == "A":
            return self.user_data_a
        if self.winner == "B":
            return self.user_data_b
        raise ValueError(f"Invalid winner value: {self.winner}")

    def __str__(self) -> str:
        return (
            f"SubGameResult({self.session}, "
            f"a = {self.user_data_a.intra_id}, b = {self.user_data_b.intra_id}, "
            f"winner = {self.winner})"
        )

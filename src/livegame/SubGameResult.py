from typing import Dict, Union

from accounts.models import UserDataCache
from .SubGameSession.SubGameSession import SubGameSession


class SubGameResult:
    def __init__(self, session: Union[SubGameSession, None]) -> None:
        self.session = session
        self.sid_a = None
        self.sid_b = None
        self.user_data_a = None
        self.user_data_b = None
        self.winner = None

    def to_json(self) -> dict:
        result = {}

        if self.sid_a is None:
            result["player_a"] = None
        else:
            result["player_a"] = self.user_data_a.to_json()

        if self.sid_b is None:
            result["player_b"] = None
        else:
            result["player_b"] = self.user_data_b.to_json()

        result["winner"] = self.winner

        return result

    def get_sid_of_winner(self) -> str:
        if not self.winner:
            raise ValueError("Winner is not yet determined")

        if self.winner == "A":
            return self.sid_a
        elif self.winner == "B":
            return self.sid_b
        else:
            raise ValueError(f"Invalid winner value: {self.winner}")

    def get_user_data_of_winner(self) -> UserDataCache:
        if not self.winner:
            raise ValueError("Winner is not yet determined")

        if self.winner == "A":
            return self.user_data_a
        elif self.winner == "B":
            return self.user_data_b
        else:
            raise ValueError(f"Invalid winner value: {self.winner}")

    def __str__(self) -> str:
        return (
            f"SubGameResult({self.session}, "
            f"a = {self.user_data_a.intra_id}, b = {self.user_data_b.intra_id}, "
            f"winner = {self.winner})"
        )

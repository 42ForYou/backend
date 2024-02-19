from typing import Dict, Union

from accounts.models import UserDataCache
from livegame.SubGameSession.SubGameSession import SubGameSession


class SubGameResult:
    def __init__(
        self,
        session: Union[SubGameSession, None],
        sid_a: Union[str, None],
        sid_b: Union[str, None],
        winner: Union[str, None],
    ) -> None:
        self.session = session
        self.sid_a = sid_a
        self.sid_b = sid_b
        self.winner = winner

    def to_json(self, sid_to_user_data: Dict[str, UserDataCache]) -> dict:
        result = {}

        if self.sid_a is None:
            result["player_a"] = None
        else:
            result["player_a"] = sid_to_user_data[self.sid_a].to_json()

        if self.sid_b is None:
            result["player_b"] = None
        else:
            result["player_b"] = sid_to_user_data[self.sid_b].to_json()

        result["winner"] = self.winner

        return result

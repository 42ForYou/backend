import math
from typing import List

from accounts.game_history import GameHistory


class RankStats:
    def __init__(self, final_rank: int) -> None:
        self.final_rank = final_rank
        self.n_tournaments = 0

    def to_dict(self) -> dict:
        return {"final_rank": self.final_rank, "n_tournaments": self.n_tournaments}


class TournamentStats:
    def __init__(self, n_ranks: int) -> None:
        self.n_ranks = n_ranks
        self.n_plays = 0
        self.stats = [RankStats(i) for i in range(-1, n_ranks)]

    def to_dict(self) -> dict:
        return {
            "n_ranks": self.n_ranks,
            "n_plays": self.n_plays,
            "stats": [stat.to_dict() for stat in self.stats],
        }


class GameStats:
    def __init__(self, histories: List[GameHistory]) -> None:
        self.n_dual_match = 0
        self.n_dual_wins = 0
        self.n_dual_looses = 0
        self.n_tournaments = 0
        self.tournament_stats: List[TournamentStats] = []

        for history in histories:
            self.register_history(history)

    def register_history(self, history: GameHistory) -> None:
        if history.game.is_tournament:
            self.n_tournaments += 1
            tournament_stat = self.find_tournament_stat(history.game.n_players)
            final_rank_stat = self.find_final_rank_stat(
                tournament_stat, history.game_player.rank
            )
            final_rank_stat.n_tournaments += 1
        else:
            self.n_dual_match += 1
            subgame = history.subgames[0]
            winner = subgame.winner
            winner_id = subgame.player_a.id if winner == "A" else subgame.player_b.id
            if winner_id == history.game_player.id:
                self.n_dual_wins += 1
            else:
                self.n_dual_looses += 1

    def find_tournament_stat(self, n_players):
        n_ranks = int(math.log2(n_players))

        for stat in self.tournament_stats:
            if stat.n_ranks == n_ranks:
                return stat

        self.tournament_stats.append(TournamentStats(n_ranks))
        return self.tournament_stats[-1]

    def find_final_rank_stat(self, tournament_stat: TournamentStats, final_rank: int):
        for rank_data in tournament_stat.stats:
            if rank_data.final_rank == final_rank:
                return rank_data
        raise Exception(f"{final_rank} not found in {tournament_stat}")

    def to_dict(self) -> dict:
        return {
            "n_dual_match": self.n_dual_match,
            "n_dual_wins": self.n_dual_wins,
            "n_dual_looses": self.n_dual_looses,
            "n_tournaments": self.n_tournaments,
            "tournament_stats": [stat.to_dict() for stat in self.tournament_stats],
        }

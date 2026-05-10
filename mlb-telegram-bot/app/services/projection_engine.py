"""
Projection engine interface + mock implementation.
Replace MockProjectionEngine with a real ML model later.
"""
from __future__ import annotations
import random
from abc import ABC, abstractmethod
from typing import Optional

from app.services.odds_provider import GameOdds


class BaseProjectionEngine(ABC):
    @abstractmethod
    async def project_game(self, game: GameOdds) -> "GameProjection":
        ...


class GameProjection:
    def __init__(self, home_win_prob: float, projected_total: float):
        self.home_win_prob   = max(0.01, min(0.99, home_win_prob))
        self.projected_total = projected_total

    def win_prob_for_side(self, game: GameOdds, market: str, side: str, line: Optional[float]) -> Optional[float]:
        if market == "moneyline":
            if side == game.home_team:
                return self.home_win_prob
            if side == game.away_team:
                return round(1 - self.home_win_prob, 6)
        elif market == "spread":
            if line is None:
                return None
            # Simplified: apply a logistic adjustment based on spread line
            adj = 0.5 + ((-line) * 0.035)
            if side == game.home_team:
                return round(max(0.05, min(0.95, adj)), 6)
            else:
                return round(max(0.05, min(0.95, 1 - adj)), 6)
        elif market == "totals":
            if line is None:
                return None
            if side.lower().startswith("over"):
                prob = max(0.05, min(0.95, self._total_prob(line, over=True)))
                return round(prob, 6)
            else:
                prob = max(0.05, min(0.95, self._total_prob(line, over=False)))
                return round(prob, 6)
        return None

    def _total_prob(self, line: float, over: bool) -> float:
        diff = self.projected_total - line
        prob_over = 0.5 + diff * 0.06
        return prob_over if over else 1 - prob_over


class MockProjectionEngine(BaseProjectionEngine):
    async def project_game(self, game: GameOdds) -> GameProjection:
        seed = sum(ord(c) for c in game.game_id)
        rng  = random.Random(seed)
        home_prob       = round(rng.uniform(0.40, 0.65), 4)
        projected_total = round(rng.uniform(7.5, 10.5), 1)
        return GameProjection(home_prob, projected_total)

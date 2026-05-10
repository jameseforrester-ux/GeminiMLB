from __future__ import annotations

from abc import ABC, abstractmethod
from app.models.domain import GameOdds, GameProjection


class ProjectionEngine(ABC):
    @abstractmethod
    async def project_game(self, game: GameOdds) -> GameProjection: ...


class MockProjectionEngine(ProjectionEngine):
    async def project_game(self, game: GameOdds) -> GameProjection:
        priors = {
            '1': 0.58,
            '2': 0.61,
            '3': 0.49,
        }
        home = priors.get(game.game_id, 0.50)
        return GameProjection(
            game_id=game.game_id,
            home_win_prob=home,
            away_win_prob=1 - home,
            confidence_note='Mock projection until live model is connected.',
            model_name='mock-v1',
        )

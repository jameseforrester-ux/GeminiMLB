from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from app.models.domain import GameOdds


class OddsProvider(ABC):
    @abstractmethod
    async def get_today_games(self) -> list[GameOdds]: ...


class MockOddsProvider(OddsProvider):
    async def get_today_games(self) -> list[GameOdds]:
        now = datetime.now().astimezone()
        return [
            GameOdds('1', now + timedelta(hours=2), 'Yankees', 'Red Sox', 'MockBook', 1.83, 2.05),
            GameOdds('2', now + timedelta(hours=4), 'Dodgers', 'Giants', 'MockBook', 1.74, 2.20),
            GameOdds('3', now + timedelta(hours=5), 'Blue Jays', 'Mariners', 'MockBook', 2.10, 1.80),
        ]

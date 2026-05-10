from __future__ import annotations
from dataclasses import dataclass, field
from app.models.domain import UserSettings


class InMemorySettingsStore:
    def __init__(self):
        self._store: dict[int, UserSettings] = {}

    def get(self, user_id: int) -> UserSettings:
        if user_id not in self._store:
            self._store[user_id] = UserSettings()
        return self._store[user_id]

    def update_bankroll(self, user_id: int, value: float) -> UserSettings:
        s = self.get(user_id)
        s.bankroll = max(1.0, value)
        return s

    def update_kelly(self, user_id: int, value: float) -> UserSettings:
        s = self.get(user_id)
        s.kelly_fraction = max(0.05, min(1.0, value))
        return s

    def update_min_edge(self, user_id: int, value: float) -> UserSettings:
        s = self.get(user_id)
        s.min_edge = max(0.0, min(0.5, value))
        return s

    def toggle_explanations(self, user_id: int) -> UserSettings:
        s = self.get(user_id)
        s.explanations_enabled = not s.explanations_enabled
        return s

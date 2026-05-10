from app.config import get_settings
from app.models.domain import UserSettings


class InMemorySettingsStore:
    def __init__(self):
        s = get_settings()
        self._store: dict[int, UserSettings] = {}
        self._defaults = UserSettings(
            bankroll=s.default_bankroll,
            kelly_fraction=s.default_kelly_fraction,
            min_edge=s.default_min_edge,
            explanations_enabled=False,
        )

    def get(self, user_id: int) -> UserSettings:
        if user_id not in self._store:
            self._store[user_id] = UserSettings(**self._defaults.__dict__)
        return self._store[user_id]

    def update_bankroll(self, user_id: int, bankroll: float) -> UserSettings:
        u = self.get(user_id)
        u.bankroll = max(1.0, bankroll)
        return u

    def update_kelly(self, user_id: int, fraction: float) -> UserSettings:
        u = self.get(user_id)
        u.kelly_fraction = min(max(fraction, 0.0), 1.0)
        return u

    def update_min_edge(self, user_id: int, edge: float) -> UserSettings:
        u = self.get(user_id)
        u.min_edge = min(max(edge, 0.0), 1.0)
        return u

    def toggle_explanations(self, user_id: int) -> UserSettings:
        u = self.get(user_id)
        u.explanations_enabled = not u.explanations_enabled
        return u

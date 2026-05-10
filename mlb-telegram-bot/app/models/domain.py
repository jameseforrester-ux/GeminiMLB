from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserSettings:
    bankroll: float
    kelly_fraction: float
    min_edge: float
    explanations_enabled: bool = False


@dataclass
class GameOdds:
    game_id: str
    commence_time: datetime
    away_team: str
    home_team: str
    sportsbook: str
    home_decimal_odds: float
    away_decimal_odds: float


@dataclass
class GameProjection:
    game_id: str
    home_win_prob: float
    away_win_prob: float
    confidence_note: str
    model_name: str = 'baseline-model'


@dataclass
class BetView:
    game_id: str
    matchup: str
    start_time_local: str
    side: str
    sportsbook: str
    model_prob: float
    implied_prob: float
    edge: float
    ev: float
    decimal_odds: float
    fair_decimal_odds: float
    kelly_fraction_raw: float
    kelly_fraction_used: float
    stake_amount: float
    confidence_note: str

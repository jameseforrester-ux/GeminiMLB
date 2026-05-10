from dataclasses import dataclass, field


@dataclass
class UserSettings:
    bankroll:             float = 1000.0
    kelly_fraction:       float = 0.5
    min_edge:             float = 0.02
    explanations_enabled: bool  = False


@dataclass
class BetView:
    game_id:              str
    matchup:              str
    start_time_local:     str
    market:               str
    side:                 str
    decimal_odds:         float
    implied_prob:         float
    model_prob:           float
    edge:                 float
    ev:                   float
    fair_decimal_odds:    float
    kelly_fraction_raw:   float
    kelly_fraction_used:  float
    stake_amount:         float
    sportsbook:           str
    confidence_note:      str
    line:                 float | None = None
    polymarket_url:       str | None   = None
    sharp_consensus:      float | None = None

"""
Betting logic: EV, Kelly sizing, value detection across ML/Spread/Totals.
"""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.services.odds_provider import GameOdds, MarketOdds
from app.services.projection_engine import BaseProjectionEngine

logger = logging.getLogger(__name__)


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
    line:                 Optional[float] = None
    polymarket_url:       Optional[str]   = None
    sharp_consensus:      Optional[float] = None


def american_to_decimal(american: int) -> float:
    if american > 0:
        return round(american / 100 + 1, 4)
    return round(100 / abs(american) + 1, 4)


def decimal_to_implied(dec: float) -> float:
    return round(1 / dec, 6) if dec > 0 else 0.5


def kelly(p: float, dec_odds: float) -> float:
    """Full Kelly fraction."""
    b = dec_odds - 1
    if b <= 0:
        return 0.0
    k = (b * p - (1 - p)) / b
    return max(0.0, round(k, 6))


class BettingService:
    def __init__(self, projection_engine: BaseProjectionEngine):
        self.engine = projection_engine

    async def build_bets(
        self,
        games: list[GameOdds],
        bankroll: float,
        kelly_fraction: float,
        min_edge: float,
    ) -> list[BetView]:
        tasks = [self._evaluate_game(g, bankroll, kelly_fraction, min_edge) for g in games]
        results = await asyncio.gather(*tasks)
        bets = [b for sub in results for b in sub]
        bets.sort(key=lambda b: b.edge, reverse=True)
        return bets

    async def _evaluate_game(
        self,
        game: GameOdds,
        bankroll: float,
        kelly_fraction: float,
        min_edge: float,
    ) -> list[BetView]:
        try:
            projection = await self.engine.project_game(game)
        except Exception as exc:
            logger.warning("Projection error for %s: %s", game.game_id, exc)
            return []

        bets: list[BetView] = []
        seen: set[tuple] = set()

        # Group markets by (market_type, side/line) and pick best-odds book
        grouped: dict[tuple, MarketOdds] = {}
        for m in game.markets:
            key = (m.market, m.side, m.line)
            if key not in grouped or m.decimal_odds > grouped[key].decimal_odds:
                grouped[key] = m

        for (mkt_type, side, line), m in grouped.items():
            dedup_key = (game.game_id, mkt_type, side, line)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            model_prob = projection.win_prob_for_side(game, mkt_type, side, line)
            if model_prob is None:
                continue

            impl_prob    = decimal_to_implied(m.decimal_odds)
            edge         = round(model_prob - impl_prob, 6)
            ev           = round(model_prob * (m.decimal_odds - 1) - (1 - model_prob), 6)
            fair_dec     = round(1 / model_prob, 4) if model_prob > 0 else 99.0
            k_raw        = kelly(model_prob, m.decimal_odds)
            k_used       = round(k_raw * kelly_fraction, 6)
            stake        = round(bankroll * k_used, 2)

            if edge < min_edge:
                continue

            start_str = game.commence_time.astimezone().strftime("%I:%M %p %Z")
            matchup   = f"{game.away_team} @ {game.home_team}"

            note = _build_confidence_note(edge, ev, k_raw, game.sharp_consensus, mkt_type)

            bets.append(BetView(
                game_id             = game.game_id,
                matchup             = matchup,
                start_time_local    = start_str,
                market              = mkt_type,
                side                = side,
                decimal_odds        = m.decimal_odds,
                implied_prob        = impl_prob,
                model_prob          = model_prob,
                edge                = edge,
                ev                  = ev,
                fair_decimal_odds   = fair_dec,
                kelly_fraction_raw  = k_raw,
                kelly_fraction_used = k_used,
                stake_amount        = stake,
                sportsbook          = m.sportsbook,
                confidence_note     = note,
                line                = line,
                polymarket_url      = game.polymarket_url,
                sharp_consensus     = game.sharp_consensus,
            ))
        return bets


def _build_confidence_note(edge: float, ev: float, k_raw: float, sharp_consensus: Optional[float], market: str) -> str:
    parts = []
    if edge >= 0.08:
        parts.append("Strong edge")
    elif edge >= 0.04:
        parts.append("Moderate edge")
    else:
        parts.append("Marginal edge")
    if ev >= 0.05:
        parts.append("high EV")
    if k_raw > 0.15:
        parts.append("large Kelly — consider fractional")
    if sharp_consensus is not None and market == "moneyline":
        parts.append(f"sharp consensus {sharp_consensus:.1%}")
    return "; ".join(parts) if parts else "Value flagged"

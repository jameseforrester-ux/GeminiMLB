"""
Odds providers:
  - TheOddsAPIProvider  : live sportsbook odds (ML, Spread, Totals) via The Odds API
  - PolymarketProvider  : Polymarket MLB game market prices via Gamma + CLOB public APIs
  - CombinedOddsProvider: merges both; primary = Polymarket, reference = sharp books
"""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

ODDS_API_BASE   = "https://api.the-odds-api.com/v4"
GAMMA_API_BASE  = "https://gamma-api.polymarket.com"
CLOB_API_BASE   = "https://clob.polymarket.com"


@dataclass
class MarketOdds:
    market:          str           # "moneyline" | "spread" | "totals"
    side:            str           # e.g. "New York Yankees" / "Over 8.5"
    decimal_odds:    float
    implied_prob:    float
    sportsbook:      str
    line:            Optional[float] = None   # spread or total line
    liquidity:       Optional[float] = None   # Polymarket only


@dataclass
class GameOdds:
    game_id:         str
    home_team:       str
    away_team:       str
    commence_time:   datetime
    markets:         list[MarketOdds] = field(default_factory=list)
    polymarket_url:  Optional[str]    = None
    sharp_consensus: Optional[float]  = None   # sharp-book home win prob


# ─────────────────────────────────────────────────────────────────────────────
# The Odds API  (sportsbook reference lines)
# ─────────────────────────────────────────────────────────────────────────────
class TheOddsAPIProvider:
    SHARP_BOOKS = {"pinnaclesports", "pinnacle", "betfair_ex_us", "draftkings", "fanduel"}
    MLB_SPORT   = "baseball_mlb"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_today_games(self) -> list[GameOdds]:
        games: list[GameOdds] = []
        async with aiohttp.ClientSession() as session:
            for market in ("h2h", "spreads", "totals"):
                url = f"{ODDS_API_BASE}/sports/{self.MLB_SPORT}/odds"
                params = {
                    "apiKey":    self.api_key,
                    "regions":   "us",
                    "markets":   market,
                    "oddsFormat":"decimal",
                    "dateFormat":"iso",
                }
                try:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                        if r.status == 401:
                            logger.error("Odds API: invalid API key")
                            break
                        r.raise_for_status()
                        data = await r.json()
                except Exception as exc:
                    logger.error("Odds API fetch error (%s): %s", market, exc)
                    continue
                self._parse_market(data, market, games)
        return games

    def _parse_market(self, data: list, market_type: str, games: list[GameOdds]):
        for event in data:
            game_id = event["id"]
            existing = next((g for g in games if g.game_id == game_id), None)
            if existing is None:
                try:
                    ct = datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
                except Exception:
                    ct = datetime.now(timezone.utc)
                existing = GameOdds(
                    game_id       = game_id,
                    home_team     = event["home_team"],
                    away_team     = event["away_team"],
                    commence_time = ct,
                )
                games.append(existing)

            sharp_probs: list[float] = []
            for bookmaker in event.get("bookmakers", []):
                bk_key  = bookmaker.get("key", "").lower()
                bk_name = bookmaker.get("title", bk_key)
                for mkt in bookmaker.get("markets", []):
                    for outcome in mkt.get("outcomes", []):
                        dec   = float(outcome.get("price", 2.0))
                        impl  = round(1 / dec, 4) if dec > 0 else 0.5
                        label = outcome.get("name", "")
                        point = outcome.get("point")
                        mkt_name = {"h2h": "moneyline", "spreads": "spread", "totals": "totals"}.get(market_type, market_type)
                        existing.markets.append(MarketOdds(
                            market       = mkt_name,
                            side         = label,
                            decimal_odds = dec,
                            implied_prob = impl,
                            sportsbook   = bk_name,
                            line         = point,
                        ))
                        if market_type == "h2h" and bk_key in self.SHARP_BOOKS and label == existing.home_team:
                            sharp_probs.append(impl)
            if sharp_probs:
                existing.sharp_consensus = round(sum(sharp_probs) / len(sharp_probs), 4)

    def get_best_moneyline(self, game: GameOdds, side: str) -> Optional[MarketOdds]:
        candidates = [m for m in game.markets if m.market == "moneyline" and m.side == side]
        return max(candidates, key=lambda m: m.decimal_odds, default=None)


# ─────────────────────────────────────────────────────────────────────────────
# Polymarket provider  (your actual trading venue)
# ─────────────────────────────────────────────────────────────────────────────
class PolymarketProvider:
    MLB_SLUG   = "mlb"
    BASE_GAMMA = GAMMA_API_BASE
    BASE_CLOB  = CLOB_API_BASE

    async def get_today_games(self) -> list[GameOdds]:
        """Fetch active MLB game-level markets from Polymarket Gamma API."""
        games: list[GameOdds] = []
        async with aiohttp.ClientSession() as session:
            try:
                url    = f"{self.BASE_GAMMA}/events"
                params = {
                    "tag_slug":  self.MLB_SLUG,
                    "active":    "true",
                    "closed":    "false",
                    "limit":     100,
                }
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    r.raise_for_status()
                    events = await r.json()
            except Exception as exc:
                logger.error("Polymarket Gamma fetch error: %s", exc)
                return games

            for event in events:
                game = self._parse_event(event)
                if game:
                    games.append(game)
                    # Enrich with CLOB live prices
                    await self._enrich_with_clob(session, game, event)
        return games

    def _parse_event(self, event: dict) -> Optional[GameOdds]:
        title = event.get("title", "")
        markets = event.get("markets", [])
        if not markets:
            return None
        # Try to split "Away @ Home" or "Away vs Home"
        teams = None
        for sep in [" @ ", " vs ", " vs. "]:
            if sep in title:
                parts = title.split(sep, 1)
                teams = (parts[0].strip(), parts[1].strip())
                break
        if teams is None:
            return None
        away_team, home_team = teams

        try:
            ct_str = event.get("startDate") or event.get("start_date") or ""
            ct = datetime.fromisoformat(ct_str.replace("Z", "+00:00")) if ct_str else datetime.now(timezone.utc)
        except Exception:
            ct = datetime.now(timezone.utc)

        slug = event.get("slug", "")
        pm_url = f"https://polymarket.com/event/{slug}" if slug else None

        return GameOdds(
            game_id       = str(event.get("id", slug)),
            home_team     = home_team,
            away_team     = away_team,
            commence_time = ct,
            polymarket_url= pm_url,
        )

    async def _enrich_with_clob(self, session: aiohttp.ClientSession, game: GameOdds, event: dict):
        """Fetch live orderbook mid-prices for each outcome."""
        for market in event.get("markets", []):
            condition_id = market.get("conditionId") or market.get("condition_id")
            if not condition_id:
                continue
            try:
                url = f"{self.BASE_CLOB}/midpoints"
                async with session.get(url, params={"condition_id": condition_id},
                                       timeout=aiohttp.ClientTimeout(total=6)) as r:
                    r.raise_for_status()
                    data = await r.json()
            except Exception as exc:
                logger.warning("CLOB midpoint fetch error: %s", exc)
                continue

            question = market.get("question", market.get("title", ""))
            for token_id, price_str in (data.get("midpoints") or {}).items():
                try:
                    price = float(price_str)          # 0..1 probability
                except Exception:
                    continue
                if price <= 0 or price >= 1:
                    continue
                dec_odds = round(1 / price, 4)
                # Determine outcome label from token metadata
                outcome_label = self._outcome_label(market, token_id, question)
                game.markets.append(MarketOdds(
                    market       = "moneyline",
                    side         = outcome_label,
                    decimal_odds = dec_odds,
                    implied_prob = round(price, 4),
                    sportsbook   = "Polymarket",
                    liquidity    = float(market.get("liquidityNum", 0) or 0),
                ))

    @staticmethod
    def _outcome_label(market: dict, token_id: str, fallback: str) -> str:
        for token in market.get("tokens", []):
            if str(token.get("token_id") or token.get("tokenId", "")) == str(token_id):
                return token.get("outcome", fallback)
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# Combined provider
# ─────────────────────────────────────────────────────────────────────────────
class CombinedOddsProvider:
    """Primary: Polymarket game prices. Reference: sharp sportsbook lines."""

    def __init__(self, odds_api_key: str):
        self.pm   = PolymarketProvider()
        self.toa  = TheOddsAPIProvider(odds_api_key)

    async def get_today_games(self) -> list[GameOdds]:
        pm_games, book_games = await asyncio.gather(
            self.pm.get_today_games(),
            self.toa.get_today_games(),
        )
        # Attach sharp consensus to Polymarket games where team names match
        for pm_game in pm_games:
            for bk_game in book_games:
                if self._teams_match(pm_game, bk_game):
                    pm_game.sharp_consensus = bk_game.sharp_consensus
                    # Carry over spread and totals from sharp books
                    for m in bk_game.markets:
                        if m.market in ("spread", "totals"):
                            m.sportsbook = m.sportsbook + " (ref)"
                            pm_game.markets.append(m)
                    break
        # If Polymarket returned nothing (e.g. off-season), fall back to book games
        return pm_games if pm_games else book_games

    @staticmethod
    def _teams_match(a: GameOdds, b: GameOdds) -> bool:
        def norm(s: str) -> str:
            return s.lower().split()[-1]   # last word of team name
        return norm(a.home_team) == norm(b.home_team) or norm(a.away_team) == norm(b.away_team)


# ─────────────────────────────────────────────────────────────────────────────
# Mock provider (keeps working with no keys)
# ─────────────────────────────────────────────────────────────────────────────
class MockOddsProvider:
    async def get_today_games(self) -> list[GameOdds]:
        now = datetime.now(timezone.utc)
        games = []
        matchups = [
            ("New York Yankees",   "Boston Red Sox"),
            ("Los Angeles Dodgers","San Francisco Giants"),
            ("Houston Astros",     "Texas Rangers"),
            ("Atlanta Braves",     "New York Mets"),
            ("Chicago Cubs",       "Milwaukee Brewers"),
        ]
        for i, (home, away) in enumerate(matchups):
            g = GameOdds(
                game_id       = f"mock_{i}",
                home_team     = home,
                away_team     = away,
                commence_time = now.replace(hour=18+i%4, minute=5, second=0, microsecond=0),
                polymarket_url= None,
                sharp_consensus= round(0.48 + i * 0.03, 2),
            )
            for book, odds_home, odds_away in [
                ("DraftKings", 1.91, 1.91),
                ("FanDuel",    1.89, 1.93),
                ("Polymarket", 1.96, 1.88),
            ]:
                for side, dec in [(home, odds_home), (away, odds_away)]:
                    g.markets.append(MarketOdds(
                        market="moneyline", side=side,
                        decimal_odds=dec, implied_prob=round(1/dec,4),
                        sportsbook=book,
                    ))
            g.markets.append(MarketOdds("spread", home, 1.91, 0.524, "DraftKings", line=-1.5))
            g.markets.append(MarketOdds("spread", away, 1.91, 0.524, "DraftKings", line=+1.5))
            g.markets.append(MarketOdds("totals", "Over",  1.91, 0.524, "DraftKings", line=8.5))
            g.markets.append(MarketOdds("totals", "Under", 1.91, 0.524, "DraftKings", line=8.5))
            games.append(g)
        return games

from zoneinfo import ZoneInfo
from app.config import get_settings
from app.models.domain import BetView, GameOdds
from app.services.projection_engine import ProjectionEngine
from app.utils.betting import expected_value, fair_decimal_odds, implied_probability_from_decimal, kelly_fraction


class BettingService:
    def __init__(self, projection_engine: ProjectionEngine):
        self.projection_engine = projection_engine
        self.settings = get_settings()

    async def build_bets(self, games: list[GameOdds], bankroll: float, kelly_frac: float, min_edge: float) -> list[BetView]:
        out: list[BetView] = []
        for game in games:
            proj = await self.projection_engine.project_game(game)
            candidates = [
                ('Home', game.home_team, proj.home_win_prob, game.home_decimal_odds),
                ('Away', game.away_team, proj.away_win_prob, game.away_decimal_odds),
            ]
            for side_label, team_name, prob, odds in candidates:
                implied = implied_probability_from_decimal(odds)
                edge = prob - implied
                ev = expected_value(prob, odds)
                raw_kelly = kelly_fraction(prob, odds)
                used_kelly = raw_kelly * kelly_frac
                stake = bankroll * used_kelly
                if edge >= min_edge and ev > 0:
                    out.append(BetView(
                        game_id=game.game_id,
                        matchup=f'{game.away_team} @ {game.home_team}',
                        start_time_local=game.commence_time.astimezone(ZoneInfo(self.settings.tz)).strftime('%Y-%m-%d %I:%M %p %Z'),
                        side=f'{team_name} ML',
                        sportsbook=game.sportsbook,
                        model_prob=prob,
                        implied_prob=implied,
                        edge=edge,
                        ev=ev,
                        decimal_odds=odds,
                        fair_decimal_odds=fair_decimal_odds(prob),
                        kelly_fraction_raw=raw_kelly,
                        kelly_fraction_used=used_kelly,
                        stake_amount=stake,
                        confidence_note=proj.confidence_note,
                    ))
        out.sort(key=lambda x: (x.ev, x.edge), reverse=True)
        return out

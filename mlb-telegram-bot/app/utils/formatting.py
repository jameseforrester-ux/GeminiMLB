from html import escape
from app.models.domain import BetView, UserSettings


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def money(v: float) -> str:
    return f"${v:,.2f}"


def fmt_bet_card(bet: BetView, settings: UserSettings) -> str:
    return (
        f"<b>{escape(bet.matchup)}</b>\\n"
        f"<i>{escape(bet.start_time_local)} • {escape(bet.sportsbook)}</i>\\n\\n"
        f"<b>Bet:</b> {escape(bet.side)} @ {bet.decimal_odds:.2f}\\n"
        f"<b>Model Win %:</b> {pct(bet.model_prob)}\\n"
        f"<b>Implied Win %:</b> {pct(bet.implied_prob)}\\n"
        f"<b>Edge:</b> {pct(bet.edge)}\\n"
        f"<b>EV:</b> {pct(bet.ev)}\\n"
        f"<b>Fair Odds:</b> {bet.fair_decimal_odds:.2f}\\n"
        f"<b>Kelly:</b> {pct(bet.kelly_fraction_raw)} raw • {pct(bet.kelly_fraction_used)} used\\n"
        f"<b>Stake:</b> {money(bet.stake_amount)} from bankroll {money(settings.bankroll)}\\n"
        f"<b>Note:</b> {escape(bet.confidence_note)}"
    )


def fmt_settings(settings: UserSettings) -> str:
    return (
        "<b>Your Settings</b>\\n"
        f"<b>Bankroll:</b> {money(settings.bankroll)}\\n"
        f"<b>Kelly Fraction:</b> {settings.kelly_fraction:.2f}\\n"
        f"<b>Min Edge:</b> {pct(settings.min_edge)}\\n"
        f"<b>Gemini Explanations:</b> {'On' if settings.explanations_enabled else 'Off'}"
    )

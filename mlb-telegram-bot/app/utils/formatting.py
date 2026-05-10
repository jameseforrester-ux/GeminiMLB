from html import escape
from app.services.betting_service import BetView
from app.models.domain import UserSettings

MARKET_EMOJI = {"moneyline": "💵", "spread": "📏", "totals": "📊"}


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def money(v: float) -> str:
    return f"${v:,.2f}"


def fmt_bet_card(bet: BetView, settings: UserSettings) -> str:
    emoji   = MARKET_EMOJI.get(bet.market, "🎯")
    mkt_lbl = bet.market.title()
    line_str = f" ({bet.line:+.1f})" if bet.line is not None else ""
    pm_line  = ""
    if bet.polymarket_url:
        pm_line = f'\n<a href="{escape(bet.polymarket_url)}">📈 Trade on Polymarket</a>'
    sharp_line = ""
    if bet.sharp_consensus is not None and bet.market == "moneyline":
        sharp_line = f"\n<b>Sharp Consensus:</b> {pct(bet.sharp_consensus)}"

    return (
        f"{emoji} <b>{escape(bet.matchup)}</b>\n"
        f"<i>{escape(bet.start_time_local)}</i>\n"
        f"<b>Market:</b> {mkt_lbl}{line_str} — {escape(bet.sportsbook)}\n"
        f"<b>Side:</b> {escape(bet.side)}\n"
        f"<b>Odds:</b> {bet.decimal_odds:.2f} decimal\n"
        f"<b>Model:</b> {pct(bet.model_prob)}  |  <b>Implied:</b> {pct(bet.implied_prob)}\n"
        f"<b>Edge:</b> {pct(bet.edge)}  |  <b>EV:</b> {pct(bet.ev)}"
        f"{sharp_line}\n"
        f"<b>Fair Odds:</b> {bet.fair_decimal_odds:.2f}\n"
        f"<b>Kelly:</b> {pct(bet.kelly_fraction_raw)} raw → {pct(bet.kelly_fraction_used)} used\n"
        f"<b>Stake:</b> {money(bet.stake_amount)} / {money(settings.bankroll)} bankroll\n"
        f"<i>{escape(bet.confidence_note)}</i>"
        f"{pm_line}"
    )


def fmt_settings(settings: UserSettings) -> str:
    return (
        "<b>Your Settings</b>\n"
        f"<b>Bankroll:</b> {money(settings.bankroll)}\n"
        f"<b>Kelly Fraction:</b> {settings.kelly_fraction:.2f}x\n"
        f"<b>Min Edge:</b> {pct(settings.min_edge)}\n"
        f"<b>Gemini:</b> {'On' if settings.explanations_enabled else 'Off'}"
    )

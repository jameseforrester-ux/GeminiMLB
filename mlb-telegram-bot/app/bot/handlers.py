from __future__ import annotations
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.keyboards import home_keyboard, settings_keyboard, market_keyboard
from app.services.betting_service import BettingService
from app.services.gemini_service import GeminiExplainer
from app.services.projection_engine import MockProjectionEngine
from app.services.settings_store import InMemorySettingsStore
from app.utils.formatting import fmt_bet_card, fmt_settings

settings_store    = InMemorySettingsStore()
projection_engine = MockProjectionEngine()
gemini            = GeminiExplainer()


def _build_odds_provider():
    provider = os.getenv("ODDS_PROVIDER", "mock").lower()
    odds_key  = os.getenv("ODDS_API_KEY", "")
    if provider == "combined" and odds_key:
        from app.services.odds_provider import CombinedOddsProvider
        return CombinedOddsProvider(odds_key)
    if provider == "theoddsapi" and odds_key:
        from app.services.odds_provider import TheOddsAPIProvider
        return TheOddsAPIProvider(odds_key)
    if provider == "polymarket":
        from app.services.odds_provider import PolymarketProvider
        return PolymarketProvider()
    from app.services.odds_provider import MockOddsProvider
    return MockOddsProvider()


odds_provider  = _build_odds_provider()
betting_service = BettingService(projection_engine)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>MLB Value Bot</b>\n"
        "Finds positive-EV bets across Moneyline, Spread, and Totals.\n"
        "Live Polymarket prices + sharp sportsbook consensus.\n\n"
        "Use the buttons below or type /help."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=home_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Commands</b>\n"
        "/today — Today full slate\n"
        "/bestbets — Top EV plays\n"
        "/settings — View/edit settings\n"
        "/bankroll 2500 — Set bankroll\n"
        "/kelly 0.25 — Set Kelly fraction\n"
        "/edge 0.03 — Set minimum edge\n"
        "/help — This message"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = settings_store.get(update.effective_user.id)
    await update.message.reply_text(
        fmt_settings(user), parse_mode=ParseMode.HTML,
        reply_markup=settings_keyboard(user.explanations_enabled),
    )


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_bets(update, best_only=False)


async def bestbets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_bets(update, best_only=True)


async def bankroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /bankroll 2500")
        return
    try:
        val = float(context.args[0].replace(",", "").replace("$", ""))
    except ValueError:
        await update.message.reply_text("Please provide a valid number, e.g. /bankroll 2500")
        return
    user = settings_store.update_bankroll(update.effective_user.id, val)
    await update.message.reply_text(fmt_settings(user), parse_mode=ParseMode.HTML)


async def kelly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /kelly 0.5")
        return
    try:
        val = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a decimal e.g. /kelly 0.5")
        return
    user = settings_store.update_kelly(update.effective_user.id, val)
    await update.message.reply_text(fmt_settings(user), parse_mode=ParseMode.HTML)


async def edge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /edge 0.02")
        return
    try:
        val = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a decimal e.g. /edge 0.03")
        return
    user = settings_store.update_min_edge(update.effective_user.id, val)
    await update.message.reply_text(fmt_settings(user), parse_mode=ParseMode.HTML)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data    = query.data
    user    = settings_store.get(user_id)

    if data in {"home", "refresh"}:
        await query.edit_message_text(
            "<b>MLB Value Bot</b>\nUse the buttons below.",
            parse_mode=ParseMode.HTML, reply_markup=home_keyboard(),
        )
    elif data == "today":
        await _send_bets(update, best_only=False, edit=True)
    elif data == "bestbets":
        await _send_bets(update, best_only=True, edit=True)
    elif data == "settings":
        await query.edit_message_text(
            fmt_settings(user), parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(user.explanations_enabled),
        )
    elif data == "toggle_gemini":
        user = settings_store.toggle_explanations(user_id)
        await query.edit_message_text(
            fmt_settings(user), parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(user.explanations_enabled),
        )
    elif data == "set_bankroll":
        await query.edit_message_text("Send /bankroll 2500 with your amount.", parse_mode=ParseMode.HTML)
    elif data == "set_kelly":
        await query.edit_message_text(
            "Send /kelly 0.5 (half Kelly) or /kelly 0.25 (quarter Kelly).", parse_mode=ParseMode.HTML)
    elif data == "set_edge":
        await query.edit_message_text(
            "Send /edge 0.03 to require at least 3% edge.", parse_mode=ParseMode.HTML)


async def _send_bets(update: Update, best_only: bool, edit: bool = False):
    user  = settings_store.get(update.effective_user.id)
    games = await odds_provider.get_today_games()
    bets  = await betting_service.build_bets(games, user.bankroll, user.kelly_fraction, user.min_edge)
    if best_only:
        bets = bets[:5]

    if not bets:
        text = "No bets meet your current settings. Try /edge 0.01 to lower the threshold."
        _target_send = _get_sender(update, edit)
        await _target_send(text, reply_markup=home_keyboard())
        return

    header = "<b>Best Bets</b>" if best_only else "<b>Today's Slate</b>"
    header += f" — {len(bets)} play(s) found"

    for i, bet in enumerate(bets):
        extra = ""
        if user.explanations_enabled:
            explanation = await gemini.explain_bet(
                bet.matchup, bet.model_prob, bet.implied_prob, bet.edge, bet.confidence_note
            )
            extra = "\n\n<b>Gemini Analysis:</b> " + explanation

        body = (header + "\n\n" + fmt_bet_card(bet, user) + extra) if i == 0 else (fmt_bet_card(bet, user) + extra)
        kb   = market_keyboard(bet.polymarket_url) if i > 0 else home_keyboard()

        if edit and i == 0 and update.callback_query:
            await update.callback_query.edit_message_text(body, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            target = update.callback_query.message if update.callback_query else update.message
            await target.reply_text(body, parse_mode=ParseMode.HTML, reply_markup=kb)


def _get_sender(update: Update, edit: bool):
    async def via_edit(text, **kwargs):
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text, **kwargs)
        else:
            m = update.callback_query.message if update.callback_query else update.message
            await m.reply_text(text, **kwargs)
    return via_edit

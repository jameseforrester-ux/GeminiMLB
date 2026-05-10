from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.keyboards import home_keyboard, settings_keyboard
from app.services.betting_service import BettingService
from app.services.gemini_service import GeminiExplainer
from app.services.odds_provider import MockOddsProvider
from app.services.projection_engine import MockProjectionEngine
from app.services.settings_store import InMemorySettingsStore
from app.utils.formatting import fmt_bet_card, fmt_settings

settings_store = InMemorySettingsStore()
odds_provider = MockOddsProvider()
projection_engine = MockProjectionEngine()
betting_service = BettingService(projection_engine)
gemini = GeminiExplainer()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        '<b>MLB Value Bot</b>\\n'
        'Track positive EV baseball bets with bankroll-aware Kelly sizing, inline actions, and optional Gemini explanations.'
    )
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=home_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        '<b>Commands</b>\\n'
        '/today - Today\\'s slate\\n'
        '/bestbets - Positive EV bets\\n'
        '/settings - Show your settings\\n'
        '/bankroll 1000 - Set bankroll\\n'
        '/kelly 0.5 - Set fractional Kelly\\n'
        '/edge 0.02 - Set minimum edge threshold'
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = settings_store.get(update.effective_user.id)
    await update.message.reply_text(
        fmt_settings(user),
        parse_mode=ParseMode.HTML,
        reply_markup=settings_keyboard(user.explanations_enabled),
    )


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_bets(update, best_only=False)


async def bestbets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_bets(update, best_only=True)


async def bankroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Usage: /bankroll 1000')
        return
    user = settings_store.update_bankroll(update.effective_user.id, float(context.args[0]))
    await update.message.reply_text(fmt_settings(user), parse_mode=ParseMode.HTML)


async def kelly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Usage: /kelly 0.5')
        return
    user = settings_store.update_kelly(update.effective_user.id, float(context.args[0]))
    await update.message.reply_text(fmt_settings(user), parse_mode=ParseMode.HTML)


async def edge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Usage: /edge 0.02')
        return
    user = settings_store.update_min_edge(update.effective_user.id, float(context.args[0]))
    await update.message.reply_text(fmt_settings(user), parse_mode=ParseMode.HTML)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    user = settings_store.get(user_id)

    if data in {'home', 'refresh'}:
        await query.edit_message_text(
            '<b>MLB Value Bot</b>\\nUse the buttons below.',
            parse_mode=ParseMode.HTML,
            reply_markup=home_keyboard(),
        )
    elif data == 'today':
        await _send_bets(update, best_only=False, edit=True)
    elif data == 'bestbets':
        await _send_bets(update, best_only=True, edit=True)
    elif data == 'settings':
        await query.edit_message_text(
            fmt_settings(user),
            parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(user.explanations_enabled),
        )
    elif data == 'toggle_gemini':
        user = settings_store.toggle_explanations(user_id)
        await query.edit_message_text(
            fmt_settings(user),
            parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(user.explanations_enabled),
        )
    elif data == 'set_bankroll':
        await query.edit_message_text('Send /bankroll 1000 with your preferred bankroll.', parse_mode=ParseMode.HTML)
    elif data == 'set_kelly':
        await query.edit_message_text('Send /kelly 0.5 for half Kelly, /kelly 0.25 for quarter Kelly.', parse_mode=ParseMode.HTML)
    elif data == 'set_edge':
        await query.edit_message_text('Send /edge 0.02 to require at least a 2% model edge.', parse_mode=ParseMode.HTML)


async def _send_bets(update: Update, best_only: bool, edit: bool = False):
    user = settings_store.get(update.effective_user.id)
    games = await odds_provider.get_today_games()
    bets = await betting_service.build_bets(games, user.bankroll, user.kelly_fraction, user.min_edge)

    if best_only:
        bets = bets[:5]

    if not bets:
        text = 'No positive EV bets met your current settings.'
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=home_keyboard())
        else:
            await update.message.reply_text(text, reply_markup=home_keyboard())
        return

    header = '<b>Best Bets</b>' if best_only else '<b>Today\\'s Card</b>'
    first = True
    for bet in bets:
        extra = ''
        if user.explanations_enabled:
            extra = '\\n\\n<b>Gemini:</b> ' + await gemini.explain_bet(bet.matchup, bet.model_prob, bet.implied_prob, bet.edge, bet.confidence_note)
        body = header + '\\n\\n' + fmt_bet_card(bet, user) + extra if first else fmt_bet_card(bet, user) + extra
        if edit and first and update.callback_query:
            await update.callback_query.edit_message_text(body, parse_mode=ParseMode.HTML, reply_markup=home_keyboard())
        else:
            target = update.callback_query.message if update.callback_query else update.message
            await target.reply_text(body, parse_mode=ParseMode.HTML, reply_markup=home_keyboard() if first else None)
        first = False

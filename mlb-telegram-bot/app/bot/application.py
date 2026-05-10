from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.bot.handlers import (
    bankroll_command,
    bestbets_command,
    callback_router,
    edge_command,
    help_command,
    kelly_command,
    settings_command,
    start,
    today_command,
)
from app.config import get_settings


def build_application() -> Application:
    settings = get_settings()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('today', today_command))
    app.add_handler(CommandHandler('bestbets', bestbets_command))
    app.add_handler(CommandHandler('settings', settings_command))
    app.add_handler(CommandHandler('bankroll', bankroll_command))
    app.add_handler(CommandHandler('kelly', kelly_command))
    app.add_handler(CommandHandler('edge', edge_command))
    app.add_handler(CallbackQueryHandler(callback_router))
    return app

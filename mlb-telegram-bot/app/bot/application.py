from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
)
from app.bot.handlers import (
    start, help_command, settings_command,
    today_command, bestbets_command,
    bankroll_command, kelly_command, edge_command,
    callback_router,
)


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("today",    today_command))
    app.add_handler(CommandHandler("bestbets", bestbets_command))
    app.add_handler(CommandHandler("bankroll", bankroll_command))
    app.add_handler(CommandHandler("kelly",    kelly_command))
    app.add_handler(CommandHandler("edge",     edge_command))
    app.add_handler(CallbackQueryHandler(callback_router))
    return app

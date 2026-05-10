from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Today', callback_data='today'), InlineKeyboardButton('Best Bets', callback_data='bestbets')],
        [InlineKeyboardButton('Settings', callback_data='settings'), InlineKeyboardButton('Refresh', callback_data='refresh')],
    ])


def settings_keyboard(explanations_enabled: bool) -> InlineKeyboardMarkup:
    label = 'Gemini: ON' if explanations_enabled else 'Gemini: OFF'
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Set Bankroll', callback_data='set_bankroll'), InlineKeyboardButton('Set Kelly', callback_data='set_kelly')],
        [InlineKeyboardButton('Set Min Edge', callback_data='set_edge'), InlineKeyboardButton(label, callback_data='toggle_gemini')],
        [InlineKeyboardButton('Back', callback_data='home')],
    ])

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚾ Today",      callback_data="today"),
            InlineKeyboardButton("🔥 Best Bets",  callback_data="bestbets"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings",   callback_data="settings"),
            InlineKeyboardButton("🔄 Refresh",    callback_data="refresh"),
        ],
    ])


def settings_keyboard(explanations_on: bool) -> InlineKeyboardMarkup:
    gem_label = "🤖 Gemini: ON" if explanations_on else "🤖 Gemini: OFF"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(gem_label,         callback_data="toggle_gemini")],
        [InlineKeyboardButton("💰 Set Bankroll",  callback_data="set_bankroll")],
        [InlineKeyboardButton("📐 Set Kelly",     callback_data="set_kelly")],
        [InlineKeyboardButton("📊 Set Min Edge",  callback_data="set_edge")],
        [InlineKeyboardButton("🏠 Home",          callback_data="home")],
    ])


def market_keyboard(polymarket_url: str | None) -> InlineKeyboardMarkup:
    rows = []
    if polymarket_url:
        rows.append([InlineKeyboardButton("📈 Trade on Polymarket", url=polymarket_url)])
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    return InlineKeyboardMarkup(rows)

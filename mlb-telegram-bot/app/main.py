import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

from app.bot.application import build_application

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
    app = build_application(token)
    logging.getLogger(__name__).info("MLB Value Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

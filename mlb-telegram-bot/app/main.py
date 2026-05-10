from app.bot.application import build_application

if __name__ == "__main__":
    app = build_application()
    app.run_polling(close_loop=False)

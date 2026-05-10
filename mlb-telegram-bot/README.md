# MLB Value Bot

A production-ready Telegram bot scaffold for MLB betting analysis with value detection, EV display, Kelly sizing, inline buttons, bankroll settings, and optional Gemini-powered explanations.

## What this bot does

- Pulls today's MLB slate from an odds provider.
- Computes fair win probabilities from a pluggable prediction engine.
- Compares model probability vs sportsbook implied probability.
- Displays edge, EV, fair odds, and Kelly stake sizing.
- Supports inline keyboard navigation for readability.
- Stores user bankroll and Kelly fraction settings.
- Supports optional Gemini explanation mode.
- Includes a mock provider so you can run it before wiring real APIs.

## Current status

This repository is a fully fleshed-out scaffold with working bot flows, settings, formatting, callback buttons, and bankroll logic. Real MLB data and model connectors are intentionally abstracted behind provider interfaces so you can plug in The Odds API, SportsDataIO, pybaseball/Statcast, and Gemini keys later without rewriting the bot surface.

## Quick start

1. Create a Telegram bot with BotFather and get your bot token.
2. Copy `.env.example` to `.env`.
3. Fill in `TELEGRAM_BOT_TOKEN`.
4. Optionally fill odds and Gemini keys later.
5. Install dependencies.
6. Run the bot.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

## Core commands

- `/start` - Welcome message and navigation.
- `/today` - Today's games and value spots.
- `/bestbets` - Filtered positive EV opportunities.
- `/settings` - Set bankroll, Kelly fraction, min edge, and explanation mode.
- `/bankroll 1000` - Set bankroll.
- `/kelly 0.5` - Set fractional Kelly.
- `/edge 0.02` - Set minimum edge threshold.
- `/help` - Help screen.

## Inline buttons

The bot uses inline keyboards as recommended by python-telegram-bot examples, where each button emits callback data handled by callback query handlers. Telegram bots also support HTML formatting for readable output, which this bot uses for structured messages. Kelly sizing is computed from the standard bankroll-management formula based on odds and estimated probability. [web:52][web:59][web:63]

## Suggested production integrations

- Odds: The Odds API or SportsDataIO.
- Baseball stats/features: pybaseball + Statcast/Baseball Savant.
- Explanations: Google Gemini via function calling.
- Storage: SQLite for local, Postgres for cloud.
- Scheduling: APScheduler or cron/systemd timers.

## Deployment roadmap

1. Run locally with the mock provider.
2. Connect a real odds provider.
3. Connect a trained model.
4. Add Gemini explanation calls.
5. Deploy to a VPS with systemd.
6. Add logging, alerts, and CLV tracking.

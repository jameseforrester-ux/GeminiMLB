# Step-by-step setup after download

## 1) Create the GitHub repo

1. Download the project folder.
2. Create a new empty GitHub repository.
3. Upload all files from this project root.
4. Clone the repo onto your VPS or local dev machine.

## 2) Create your Telegram bot

1. Open Telegram and message BotFather.
2. Run `/newbot`.
3. Choose a name and username.
4. Copy the bot token.
5. Paste it into `.env` as `TELEGRAM_BOT_TOKEN=...`.

## 3) Prepare the environment

```bash
cd mlb-telegram-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Required first pass:

```env
TELEGRAM_BOT_TOKEN=your_real_token
ODDS_PROVIDER=mock
DEFAULT_BANKROLL=1000
DEFAULT_KELLY_FRACTION=0.50
DEFAULT_MIN_EDGE=0.02
TZ=America/Vancouver
```

## 4) First local run

```bash
python -m app.main
```

Then open Telegram and test:

- `/start`
- `/today`
- `/bestbets`
- `/settings`
- `/bankroll 2500`
- `/kelly 0.25`
- `/edge 0.03`

## 5) Push to GitHub

```bash
git init
git add .
git commit -m "Initial MLB value bot scaffold"
git branch -M main
git remote add origin YOUR_GITHUB_URL
git push -u origin main
```

## 6) Connect a real odds API

### Option A: The Odds API

1. Get your API key.
2. Put it in `.env` as `ODDS_API_KEY=...`.
3. Set `ODDS_PROVIDER=theoddsapi`.
4. Replace `MockOddsProvider` with a real implementation in `app/services/odds_provider.py`.

Recommended endpoint plan:
- Current MLB odds.
- Historical odds or closing odds for CLV tracking.
- Market/bookmaker selection.

## 7) Connect pybaseball and Statcast

Use `pybaseball` to build rolling features such as:
- Starter strikeout rate.
- Starter velocity trend.
- Hard-hit rate allowed.
- Barrel rate allowed.
- Team OPS or wOBA over last 7, 14, and 30 days.
- Bullpen workload over last 3 days.

Recommended code location:
- `app/data/feature_builder.py`
- `app/models/train_moneyline_model.py`
- `app/models/predict.py`

Suggested rollout:
1. Start with game-level historical rows.
2. Add starter-based features.
3. Add team rolling offense.
4. Add bullpen rest.
5. Add park/weather.
6. Add line movement and market consensus.
7. Calibrate probabilities with isotonic or Platt scaling.

## 8) Add Gemini explanations

1. Get a Gemini API key.
2. Add `GEMINI_API_KEY=...` to `.env`.
3. Expand `app/services/gemini_service.py`.
4. Pass structured inputs only: matchup, price, model probability, edge, EV, and top features.
5. Keep Gemini as an explainer, not the source of truth for pricing.

Best use cases:
- Explain why a bet qualifies.
- Summarize lineup/injury/news context.
- Parse natural-language user questions.
- Generate concise pregame alert wording.

## 9) Add persistence

Right now settings are in memory. For production:

- Add SQLite first.
- Then upgrade to Postgres if needed.

Tables to add:
- users
- user_settings
- predictions
- odds_snapshots
- clv_results
- alerts_log

## 10) Production deployment with systemd

### Create service file

```ini
[Unit]
Description=MLB Value Bot
After=network.target

[Service]
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/mlb-telegram-bot
EnvironmentFile=/home/YOUR_USER/mlb-telegram-bot/.env
ExecStart=/home/YOUR_USER/mlb-telegram-bot/.venv/bin/python -m app.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Enable it

```bash
sudo cp mlb-value-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mlb-value-bot
sudo systemctl start mlb-value-bot
sudo systemctl status mlb-value-bot --no-pager
```

## 11) Immediate upgrades I recommend next

1. Real odds provider.
2. SQLite storage.
3. Prediction logging.
4. CLV report command.
5. Scheduled alerts 60 minutes before first pitch.
6. Gemini explanation quality pass.
7. Model training pipeline from pybaseball/Statcast features.

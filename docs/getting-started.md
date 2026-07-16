# Getting Started

This guide gets the DatsDefense Strategy Bot running against a live round.

## 1. Prerequisites

- Python 3.10+
- A DatsTeam account and a **team token** for the `zombidef` game
- The `requests` and `matplotlib` packages

## 2. Install

```bash
git clone https://github.com/simeonkolchin/datsdefense-strategy-bot.git
cd datsdefense-strategy-bot
python -m venv .venv && source .venv/bin/activate
pip install requests matplotlib
```

## 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and set `DATS_TOKEN` to your team token. The bot reads it via `os.environ`, so load the file into your shell before running:

```bash
export $(grep -v '^#' .env | xargs)
```

(Or use a tool like [`direnv`](https://direnv.net/) / `python-dotenv`.)

## 4. Run

```bash
python main.py
```

You should see:

- HTTP status lines as the bot registers (`PUT /participate`) and polls (`GET /units`, `GET /world`).
- `attack -` / `BUILD:` / `ATTACK BASE:` prints as the strategy fires each tick.
- `game_log.txt` accumulating timestamped events.
- `game_map_visualized.png` refreshed every tick with the current board.
- Per-turn snapshots written to `games/<hour>_<minute>_<n>.json`.

## 5. Replay offline (no live round)

Set `DEBUG = True` at the top of `main.py`. The bot then reads saved rounds from `games/` instead of the network, which is handy for tuning the strategy without burning a live game. `debug_gamestate.py` also holds a hard-coded `LOCAL_GAME_STATE` sample you can inspect.

## 6. Check the round schedule

```bash
python check.py
```

This calls `GET /rounds/zombidef` and prints the available rounds so you know when to be online.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401` / registration fails | `DATS_TOKEN` is missing or wrong — re-check `.env` and that it's exported. |
| No map image | Ensure `matplotlib` is installed and the process has write permission in the repo dir. |
| Empty `games/` | The directory must exist (it ships with a `.gitkeep`); snapshots are only written when `DEBUG` is `False`. |

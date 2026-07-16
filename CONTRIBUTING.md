# Contributing

Thanks for your interest in improving the DatsDefense Strategy Bot!

## Getting set up

```bash
git clone https://github.com/simeonkolchin/datsdefense-strategy-bot.git
cd datsdefense-strategy-bot
python -m venv .venv && source .venv/bin/activate
pip install requests matplotlib ruff
cp .env.example .env   # add your DATS_TOKEN
```

## Ground rules

- **Never commit secrets.** Your `DATS_TOKEN` belongs in `.env` (gitignored), never in code.
- Keep the bot runnable with a single `python main.py`.
- The project is intentionally small — prefer clear, self-contained functions over frameworks.

## Before opening a PR

- Run the linter: `ruff check .`
- Test your strategy changes against saved rounds by setting `DEBUG = True` in `main.py` and replaying JSON from `games/`.
- Describe the behavioural change (what the bot now does differently) in the PR body.

## Reporting bugs

Open an issue with the round conditions, the relevant log lines from `game_log.txt`, and a rendered `game_map_visualized.png` if it helps illustrate the problem.

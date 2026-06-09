# Reddit Trend Reporter

Scheduled Reddit trend collection with a static interactive report.

This repo separates the repeatable parts from the LLM part:

- `scripts/collect_reddit.py` collects subreddit listings through `rdt-cli`.
- `scripts/run_claude_report.py` sends a compact snapshot to `claude -p` and writes structured analysis JSON.
- `src/` renders `public/data/latest.json` as an interactive Vite/React static page.
- `scripts/pipeline.py` runs collect -> Claude report -> static build.

## Local setup

```bash
npm install
```

Install and authenticate `rdt-cli` on the machine that will run the schedule. If Reddit is logged into a non-default Chrome profile, create the credential file manually or patch `rdt-cli` to read that profile.

```bash
uv tool install rdt-cli
rdt status --json
```

Claude Code must also be available for the LLM report step:

```bash
claude --version
```

## Run once

```bash
npm run pipeline
```

If you want to test without calling Claude:

```bash
npm run pipeline -- --skip-llm
```

If Claude fails but you still want a build artifact:

```bash
npm run pipeline -- --allow-fallback
```

## Configure targets

Edit `config/reddit-report.json`.

```json
{
  "subreddits": ["StableDiffusion"],
  "sort": "top",
  "time": "week",
  "limit": 30,
  "output": "public/data/latest.json",
  "history_dir": "data/runs"
}
```

`time` can be `hour`, `day`, `week`, `month`, `year`, or `all`, matching Reddit top listing filters.

## Scheduled execution

On the machine that has Reddit cookies and Claude access, use cron:

```cron
0 9 * * * cd /path/to/reddit-trend-reporter && npm run pipeline -- --allow-fallback >> logs/pipeline.log 2>&1
```

For weekly Monday runs:

```cron
0 9 * * 1 cd /path/to/reddit-trend-reporter && npm run pipeline -- --allow-fallback >> logs/pipeline.log 2>&1
```

If you want the scheduled machine to publish results back to GitHub Pages:

```bash
git pull --ff-only
npm run pipeline -- --allow-fallback
git add public/data/latest.json data/runs
git commit -m "Update Reddit trend report"
git push
```

## GitHub Pages

This repo includes a GitHub Actions workflow that builds the Vite app and publishes `dist/` to GitHub Pages on every push to `main`.

The workflow does not collect Reddit data, because Reddit cookies and Claude credentials should live on the scheduled machine. The scheduled machine should commit updated JSON data back to the repo, then GitHub Pages will rebuild.

## Development

```bash
npm run dev
```

Open the printed localhost URL.

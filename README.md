# Reddit Trend Reporter

Scheduled Reddit trend collection with a static interactive report.

This repo separates the repeatable parts from the LLM part:

- The `reddit_trend_reporter` Python package (CLI: `reddit-report`) collects
  subreddit listings — and configurable top posts/comments — through `rdt-cli`.
- `reddit-report report` sends a compact snapshot to `claude -p` and writes
  trend, community voice, and commercial decision JSON.
- `reddit-report pipeline` runs collect -> Claude report (-> optional build).
- `src/` renders `public/data/latest.json`, report archives, and commercial
  decision notes as an interactive Vite/React static page.

The data pipeline (Python) and the web app (Vite/React) are separable: the CLI
produces JSON data anywhere, and the repo + GitHub Pages render/deploy it.
(`scripts/*.py` remain as thin shims that call the package.)

For AI agents working on a new machine, read [`AGENTS.md`](./AGENTS.md) first. It explains the operating goal, file map, current limitations, and next implementation target.

For a plain-language explanation of the moving parts, read [`docs/how-it-works.md`](./docs/how-it-works.md).

## Install as a CLI (run anywhere)

The data pipeline is a normal Python package, so you can install it like any
other tool. `rdt-cli` is a declared dependency, so this **single command brings
the Reddit collector along** — no separate install:

```bash
# from PyPI (once published)
uv tool install reddit-trend-reporter

# or straight from git, no PyPI needed
uv tool install git+https://github.com/<you>/reddit-trend-reporter
```

Then run it from any working directory; outputs are written under the current
directory (or `--base-dir`), config is found via `--config`,
`$REDDIT_REPORT_CONFIG`, `./config/reddit-report.json`, or
`~/.config/reddit-trend-reporter/reddit-report.json`:

```bash
reddit-report init                 # scaffold ./config/reddit-report.json
reddit-report pipeline             # collect + Claude report (JSON only)
reddit-report pipeline --skip-llm  # collect only
reddit-report collect --config /path/to/my.json --base-dir /data/reddit
```

The `claude` CLI (for the report step) and the Node/Vite frontend are **not**
Python dependencies — install those separately if you need them. For local
development against the source, use `uv tool install --editable .`.

## Local setup

On a fresh machine, one command installs every dependency (npm packages, `uv`,
and `rdt-cli`) and checks for the Claude CLI:

```bash
npm run setup
```

This is idempotent. It does **not** touch Reddit/Claude credentials — you still
authenticate those yourself. If you prefer manual steps:

```bash
npm install
uv tool install rdt-cli
rdt status --json
```

> Even without any setup, `npm run pipeline` self-heals: if `rdt` is missing but
> `uv` is installed, collection falls back to `uvx --from rdt-cli rdt`, which
> downloads and caches `rdt-cli` on demand.

Authenticate `rdt-cli` on the machine that will run the schedule. If Reddit is
logged into a non-default Chrome profile, create the credential file manually or
patch `rdt-cli` to read that profile.

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

This updates:

- `public/data/latest.json` for the latest one-page summary.
- `public/data/index.json` for the report archive list.
- `public/data/reports/*.json` for individual report snapshots.
- `data/runs/*.json` for local raw history.

## Configure targets

Edit `config/reddit-report.json`.

```json
{
  "subreddits": ["StableDiffusion"],
  "sort": "top",
  "time": "day",
  "limit": 30,
  "read_top_posts": 8,
  "max_comments_per_post": 12,
  "comment_depth": 1,
  "trending": { "sort": "rising", "limit": 15 },
  "output": "public/data/latest.json",
  "history_dir": "data/runs"
}
```

`time` can be `hour`, `day`, `week`, `month`, `year`, or `all`, matching Reddit top listing filters. Use `day` for a daily cadence; `week` for a weekly one.

`trending` (optional) collects a second, lighter listing per subreddit to surface what's gaining momentum right now — separate from the established top posts. `sort` accepts `rising` (default), `hot`, `new`, etc. Remove the block to skip trending collection. Rising posts appear in a "Trending" section on the Live Report and are fed into the Claude analysis.

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
git add public/data data/runs
git commit -m "Update Reddit trend report"
git push
```

## GitHub Pages

This repo includes a GitHub Actions workflow that builds the Vite app and publishes `dist/` to GitHub Pages on every push to `main`.

The workflow does not collect Reddit data, because Reddit cookies and Claude credentials should live on the scheduled machine. The scheduled machine should commit updated JSON data back to the repo, then GitHub Pages will rebuild.

The published app has five operating surfaces:

- `Live Report`: the currently selected report, defaulting to latest.
- `Reports`: individual report snapshots created by scheduled runs.
- `Decision Inputs`: qualitative community voice plus conservative business-use evaluation.
- `Why`: short landing page for explaining the product.
- `How`: manual for installing on another machine and publishing to GitHub Pages.

## Long-Lived Model Knowledge

The repo includes a lightweight knowledge base for model/tool reputation:

- `knowledge/models/*.json`: cumulative qualitative notes by model name.
- `knowledge/schema/model-reputation.schema.json`: expected shape.
- `docs/roadmap.md`: next steps for comment-level collection and automatic reputation updates.

This is intended to travel with the repo. A new machine or AI agent can clone the repo, read `AGENTS.md`, and continue from the current context instead of relying on chat history.

## Development

```bash
npm run dev
```

Open the printed localhost URL.

# How It Works

This project turns Reddit activity into a scheduled, static, shareable intelligence report.

## One-Line Summary

A private machine collects Reddit data and asks Claude to analyze it; GitHub stores the resulting JSON files; GitHub Pages builds and serves the interactive website.

## Roles

### 1. Report Generation Machine

This is the only machine that needs private runtime access:

- Reddit browser cookies or `rdt-cli` credentials.
- `claude -p` access.
- Cron or another scheduler.
- Git push permission to the repo.

It runs:

```bash
npm run pipeline -- --allow-fallback
```

That command does all report-generation work locally on that machine.

### 2. GitHub Repository

The repo is the source of truth for:

- Code.
- Static website.
- Latest report data.
- Report history.
- Long-lived model reputation knowledge.
- Agent instructions.

Generated files committed back to GitHub include:

- `public/data/latest.json`
- `public/data/index.json`
- `public/data/reports/*.json`
- `data/runs/*.json`
- future: `knowledge/models/*.json` updates

### 3. GitHub Pages

GitHub Pages does not collect Reddit data and does not call Claude.

It only:

1. Receives a push to `main`.
2. Runs `npm ci`.
3. Runs `npm run build`.
4. Publishes `dist/`.

That means deployment can happen from anywhere, as long as the generated JSON files are pushed to GitHub.

## Pipeline Flow

```text
cron on private machine
  -> npm run pipeline -- --allow-fallback
  -> scripts/collect_reddit.py
  -> rdt-cli reads Reddit
  -> public/data/latest.json
  -> scripts/run_claude_report.py
  -> claude -p writes analysis + commercial decision
  -> public/data/reports/<timestamp>.json
  -> public/data/index.json
  -> npm run build
  -> git add public/data data/runs knowledge/models
  -> git commit
  -> git push
  -> GitHub Actions
  -> GitHub Pages
```

## What the Website Reads

The static app has no server. It loads JSON files from GitHub Pages:

- `data/latest.json`: latest selected report.
- `data/index.json`: report archive list.
- `data/reports/*.json`: individual report snapshots.

The React app renders these into tabs:

- `Product`: product landing page.
- `Live Report`: latest or selected report.
- `Reports`: report archive.
- `Commercial`: business-use decision screen.
- `Setup & Deploy`: installation and deployment guide.

## Why Collection and Deployment Are Split

Reddit access and Claude access are local/private operational concerns. GitHub Pages is public/static infrastructure.

Keeping them separate gives you:

- No Reddit cookies in GitHub Actions.
- No Claude credentials in GitHub Actions.
- Reproducible static site builds.
- Easy migration to another machine.
- A Git history of every generated report.

## How a New Machine Continues the Work

On a new machine:

```bash
git clone https://github.com/choigawoon/reddit-trend-reporter.git
cd reddit-trend-reporter
npm install
uv tool install rdt-cli
rdt status --json
claude --version
cat AGENTS.md
```

Then run:

```bash
npm run pipeline -- --allow-fallback
```

If the output looks right:

```bash
git add public/data data/runs knowledge/models
git commit -m "Update Reddit trend report"
git push
```

GitHub Pages will rebuild automatically.

## Current Limitation

The current pipeline reads post listing data and self-post text. It does not yet automatically read top comments.

The next planned step is comment-enriched collection:

```text
top posts
  -> rdt read <post_id>
  -> top comments
  -> qualitative sentiment
  -> model reputation updates
```

See `docs/roadmap.md`.

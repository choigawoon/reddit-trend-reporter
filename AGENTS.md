# Agent Operating Guide

This repo is a scheduled Reddit intelligence reporter. Treat this file as the first read for any AI agent working on a new machine.

## Product Goal

Collect Reddit community signals, read enough raw discussion to understand real user sentiment, and publish an interactive static report that supports commercial decisions.

The target workflow is:

1. Collect subreddit top posts.
2. Read selected post bodies and top comments.
3. Normalize raw material into JSON.
4. Ask `claude -p` to produce trend, qualitative sentiment, commercial opportunity, and risk analysis.
5. Update long-lived model reputation knowledge in `knowledge/models/`.
6. Build a static Vite app and deploy through GitHub Pages.

## Current State

Implemented:

- Reddit top-list collection via `rdt-cli`.
- Comment-enriched collection for configurable top posts via `rdt read <post_id>`.
- Claude headless report generation.
- Community voice qualitative analysis from post bodies and collected comments.
- Latest report JSON at `public/data/latest.json`.
- Report archive JSON at `public/data/reports/*.json`.
- Report index at `public/data/index.json`.
- Static app tabs: `Product`, `Live Report`, `Reports`, `Commercial`, `Setup & Deploy`.
- GitHub Pages deployment workflow.

Not yet implemented:

- Automatic model reputation updates.
- UI for model reputation history.
- Diffing model reputation over time.

## Important Files

- `config/reddit-report.json`: collection target settings (the `trend` profile).
- `config/profiles.json`: profile registry; `config/leaderboard.json`, `config/aigamedev.json` are scaffold profiles.
- `pyproject.toml`: packages the pipeline as the `reddit-report` CLI (depends on `rdt-cli`).
- `reddit_trend_reporter/collect.py`: repeatable Reddit listing collector + rdt resolution + trending.
- `reddit_trend_reporter/profiles.py`: per-profile prompt + schema + fallback. Add new report types here.
- `reddit_trend_reporter/report.py`: runs Claude with the profile's prompt; writes analysis back.
- `reddit_trend_reporter/manifest.py`: derives `public/data/profiles.json` (UI profile switcher) from the registry.
- `reddit_trend_reporter/pipeline.py` + `cli.py`: collect -> report -> manifest (-> optional build) and CLI wiring.
- `scripts/*.py`: thin backward-compat shims that call the package.
- `src/main.jsx`: React UI.
- `src/styles.css`: styling.
- `public/data/latest.json`: current published report.
- `public/data/index.json`: archive index.
- `public/data/reports/*.json`: individual reports.
- `data/runs/*.json`: local historical snapshots.
- `knowledge/models/*.json`: long-lived model reputation knowledge.
- `docs/roadmap.md`: planned implementation work.

## Operating Commands

```bash
npm install
npm run pipeline -- --allow-fallback
npm run build
npm run dev
```

On the scheduled machine:

```bash
git pull --ff-only
npm run pipeline -- --allow-fallback
git add public/data data/runs knowledge/models
git commit -m "Update Reddit trend report"
git push
```

## Reddit Auth Assumptions

`rdt-cli` reads authenticated Reddit cookies from the local browser or saved credential file. The scheduled machine must have:

- Reddit logged in through a browser or `~/.config/rdt-cli/credential.json`.
- `rdt status --json` showing `authenticated: true`.
- `claude --version` working.

## Data Policy

- Store post/comment excerpts only as needed for analysis.
- Preserve Reddit post IDs and comment IDs for traceability.
- Do not treat Reddit comments as legal, licensing, or financial truth.
- Commercial decisions must remain conservative when IP, NSFW, safety bypass, privacy, or licensing issues appear.

## Next Implementation Target

Add automatic model reputation updates:

```text
community_voice + reports -> update knowledge/models -> Models UI
```

See `docs/roadmap.md`.

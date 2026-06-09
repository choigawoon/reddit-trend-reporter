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
- Claude headless report generation.
- Latest report JSON at `public/data/latest.json`.
- Report archive JSON at `public/data/reports/*.json`.
- Report index at `public/data/index.json`.
- Static app tabs: `Product`, `Live Report`, `Reports`, `Commercial`, `Setup & Deploy`.
- GitHub Pages deployment workflow.

Not yet implemented:

- Comment collection with `rdt read <post_id>`.
- Comment-level sentiment/reaction analysis.
- Automatic model reputation updates.
- UI for model reputation history.
- Diffing model reputation over time.

## Important Files

- `config/reddit-report.json`: collection target settings.
- `scripts/collect_reddit.py`: repeatable Reddit listing collector.
- `scripts/run_claude_report.py`: LLM report generator. Keep prompt/schema changes here.
- `scripts/pipeline.py`: collect -> report -> build.
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

Add a comment-enriched collection step:

```text
top posts -> read top N posts -> collect body + top comments -> Claude sentiment/commercial analysis -> update knowledge/models
```

See `docs/roadmap.md`.

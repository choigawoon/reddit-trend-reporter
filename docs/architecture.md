# Architecture

## Pipeline

```text
config/reddit-report.json
  -> scripts/collect_reddit.py
  -> public/data/latest.json
  -> scripts/run_claude_report.py
  -> public/data/latest.json with analysis
  -> public/data/reports/<timestamp>.json
  -> npm run build
  -> GitHub Pages
```

## Separation of Work

Repeatable scripting:

- Calling `rdt-cli`.
- Normalizing posts.
- Writing report JSON files.
- Maintaining report archive indexes.
- Building the static site.

LLM work:

- Trend synthesis.
- Qualitative interpretation.
- Commercial opportunity/risk judgment.
- Future: comment-level sentiment and model reputation summaries.

## Static Data Contracts

`public/data/latest.json` is the current report. It contains:

- `generated_at`
- `query`
- `subreddits[].posts[]`
- `analysis`
- `analysis.commercial`

`public/data/index.json` is the report archive index. It points to:

- `public/data/reports/*.json`

`knowledge/models/*.json` is the long-lived qualitative knowledge base. It should be updated by future model-reputation jobs after comment analysis is implemented.

## Deployment

GitHub Actions only builds and deploys static files. It does not collect Reddit data. Collection requires cookies and Claude CLI, so it must run on a scheduled machine controlled by the user.

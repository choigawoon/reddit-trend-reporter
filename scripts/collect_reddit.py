#!/usr/bin/env python3
"""Deprecated shim. Prefer `reddit-report collect`
(or `python3 -m reddit_trend_reporter collect`). Kept so existing cron jobs and
docs that call `python3 scripts/collect_reddit.py` keep working."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reddit_trend_reporter.cli import run_collect

if __name__ == "__main__":
    raise SystemExit(run_collect(sys.argv[1:]))

#!/usr/bin/env python3
"""Deprecated shim. Prefer `reddit-report report`
(or `python3 -m reddit_trend_reporter report`). Kept for backward compatibility
with docs/cron that call `python3 scripts/run_claude_report.py`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reddit_trend_reporter.cli import run_report

if __name__ == "__main__":
    raise SystemExit(run_report(sys.argv[1:]))

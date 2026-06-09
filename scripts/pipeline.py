#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run collection, optional Claude analysis, and static build.")
    parser.add_argument("--skip-llm", action="store_true")
    parser.add_argument("--allow-fallback", action="store_true")
    args = parser.parse_args()

    run(["python3", "scripts/collect_reddit.py"])
    if not args.skip_llm:
        report_cmd = ["python3", "scripts/run_claude_report.py"]
        if args.allow_fallback:
            report_cmd.append("--allow-fallback")
        run(report_cmd)
    run(["npm", "run", "build"])


if __name__ == "__main__":
    main()

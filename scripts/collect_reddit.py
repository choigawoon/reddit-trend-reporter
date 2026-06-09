#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "reddit-report.json"
LOCAL_RDT = ROOT.parent / "rdt-cli"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rdt_command() -> tuple[list[str], Path]:
    if shutil.which("rdt"):
        return ["rdt"], ROOT
    if (LOCAL_RDT / "pyproject.toml").exists():
        return ["uv", "run", "rdt"], LOCAL_RDT
    return ["uv", "run", "rdt"], ROOT


def run_rdt(subreddit: str, sort: str, time_filter: str, limit: int) -> dict[str, Any]:
    base_cmd, cwd = rdt_command()
    cmd = [
        *base_cmd,
        "sub",
        subreddit,
        "-s",
        sort,
        "-t",
        time_filter,
        "-n",
        str(limit),
        "--json",
    ]
    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(f"rdt failed for r/{subreddit}: {message}") from exc
    return json.loads(raw)


def normalize_post(post: dict[str, Any], rank: int) -> dict[str, Any]:
    data = post["data"]
    created_utc = data.get("created_utc") or 0
    created_at = dt.datetime.fromtimestamp(created_utc, dt.timezone.utc).replace(microsecond=0).isoformat()
    permalink = data.get("permalink", "")
    reddit_url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink
    text = (data.get("selftext") or "").strip()
    return {
        "rank": rank,
        "id": data.get("id"),
        "fullname": data.get("name"),
        "title": data.get("title"),
        "subreddit": data.get("subreddit"),
        "author": data.get("author"),
        "score": data.get("score", data.get("ups", 0)),
        "comments": data.get("num_comments", 0),
        "upvote_ratio": data.get("upvote_ratio"),
        "flair": data.get("link_flair_text"),
        "created_at": created_at,
        "created_utc": created_utc,
        "url": data.get("url"),
        "reddit_url": reddit_url,
        "domain": data.get("domain"),
        "is_self": bool(data.get("is_self")),
        "is_video": bool(data.get("is_video")),
        "over_18": bool(data.get("over_18")),
        "text": text[:4000],
    }


def collect(config: dict[str, Any]) -> dict[str, Any]:
    report = {
        "generated_at": utc_now(),
        "source": "rdt-cli",
        "query": {
            "subreddits": config["subreddits"],
            "sort": config.get("sort", "top"),
            "time": config.get("time", "week"),
            "limit": int(config.get("limit", 30)),
        },
        "subreddits": [],
        "analysis": None,
    }
    for subreddit in config["subreddits"]:
        raw = run_rdt(subreddit, report["query"]["sort"], report["query"]["time"], report["query"]["limit"])
        listing = raw["data"]["data"]
        posts = [normalize_post(item, idx) for idx, item in enumerate(listing.get("children", []), 1)]
        report["subreddits"].append(
            {
                "name": subreddit,
                "after": listing.get("after"),
                "post_count": len(posts),
                "posts": posts,
            }
        )
    return report


def write_outputs(report: dict[str, Any], config: dict[str, Any]) -> None:
    output = ROOT / config.get("output", "public/data/latest.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    history_dir = ROOT / config.get("history_dir", "data/runs")
    history_dir.mkdir(parents=True, exist_ok=True)
    stamp = report["generated_at"].replace(":", "").replace("-", "").replace("+0000", "Z")
    history_path = history_dir / f"{stamp}.json"
    history_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {output.relative_to(ROOT)}")
    print(f"wrote {history_path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect subreddit top posts with rdt-cli.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = load_config(args.config)
    report = collect(config)
    write_outputs(report, config)


if __name__ == "__main__":
    main()

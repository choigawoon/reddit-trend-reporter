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


def run_rdt_read(post_id: str) -> dict[str, Any] | None:
    base_cmd, cwd = rdt_command()
    cmd = [*base_cmd, "read", post_id, "--json"]
    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        print(f"warning: rdt read failed for {post_id}: {message}")
        return None
    return json.loads(raw)


def normalize_comment(comment: dict[str, Any], *, depth: int, max_depth: int) -> dict[str, Any]:
    replies = []
    if depth < max_depth:
        for reply in comment.get("replies", []) or []:
            if reply.get("author") == "[more]":
                continue
            replies.append(normalize_comment(reply, depth=depth + 1, max_depth=max_depth))
    return {
        "id": comment.get("id"),
        "fullname": comment.get("fullname"),
        "author": comment.get("author"),
        "score": comment.get("score", 0),
        "body": (comment.get("body") or "").strip()[:1200],
        "created_utc": comment.get("created_utc"),
        "replies": replies,
    }


def coerce_read_detail(detail: dict[str, Any]) -> dict[str, Any]:
    data = detail.get("data")
    if isinstance(data, dict):
        return data
    if not isinstance(data, list) or len(data) < 2:
        return {}

    post = {}
    comments: list[dict[str, Any]] = []
    try:
        post_children = data[0]["data"].get("children", [])
        if post_children:
            post = normalize_post(post_children[0], rank=0)
    except (KeyError, TypeError, IndexError):
        post = {}

    try:
        comment_children = data[1]["data"].get("children", [])
    except (KeyError, TypeError, IndexError):
        comment_children = []
    for child in comment_children:
        if child.get("kind") != "t1":
            continue
        raw = child.get("data", {})
        comments.append(
            {
                "id": raw.get("id"),
                "fullname": raw.get("name"),
                "author": raw.get("author"),
                "score": raw.get("score", 0),
                "body": raw.get("body", ""),
                "created_utc": raw.get("created_utc"),
                "replies": [],
            }
        )
    return {"post": post, "comments": comments, "more_count": 0, "more_children": []}


def enrich_posts_with_discussion(posts: list[dict[str, Any]], config: dict[str, Any]) -> None:
    read_top_posts = int(config.get("read_top_posts", 0))
    max_comments = int(config.get("max_comments_per_post", 0))
    comment_depth = int(config.get("comment_depth", 1))
    if read_top_posts <= 0 or max_comments <= 0:
        return

    for post in posts[:read_top_posts]:
        detail = run_rdt_read(post["id"])
        if not detail or not detail.get("ok"):
            continue
        data = coerce_read_detail(detail)
        detailed_post = data.get("post") or {}
        if detailed_post.get("selftext"):
            post["text"] = detailed_post["selftext"][:4000]
        comments = data.get("comments", []) or []
        normalized_comments = [
            normalize_comment(comment, depth=0, max_depth=comment_depth)
            for comment in comments[:max_comments]
            if comment.get("author") != "[more]" and (comment.get("body") or "").strip()
        ]
        post["discussion"] = {
            "comments_collected": len(normalized_comments),
            "more_count": data.get("more_count", 0),
            "comments": normalized_comments,
        }


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
        "discussion": None,
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
            "read_top_posts": int(config.get("read_top_posts", 0)),
            "max_comments_per_post": int(config.get("max_comments_per_post", 0)),
            "comment_depth": int(config.get("comment_depth", 1)),
        },
        "subreddits": [],
        "analysis": None,
    }
    for subreddit in config["subreddits"]:
        raw = run_rdt(subreddit, report["query"]["sort"], report["query"]["time"], report["query"]["limit"])
        listing = raw["data"]["data"]
        posts = [normalize_post(item, idx) for idx, item in enumerate(listing.get("children", []), 1)]
        enrich_posts_with_discussion(posts, config)
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

    public_reports_dir = ROOT / config.get("public_reports_dir", "public/data/reports")
    public_reports_dir.mkdir(parents=True, exist_ok=True)
    public_report_path = public_reports_dir / f"{stamp}.json"
    public_report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    index_path = ROOT / config.get("public_index", "public/data/index.json")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text())
        except json.JSONDecodeError:
            index = {"reports": []}
    else:
        index = {"reports": []}
    entry = {
        "generated_at": report["generated_at"],
        "path": f"reports/{public_report_path.name}",
        "subreddits": report["query"]["subreddits"],
        "sort": report["query"]["sort"],
        "time": report["query"]["time"],
        "post_count": sum(sub["post_count"] for sub in report["subreddits"]),
    }
    reports = [item for item in index.get("reports", []) if item.get("path") != entry["path"]]
    reports.insert(0, entry)
    index["reports"] = reports[:100]
    index["latest"] = entry
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {output.relative_to(ROOT)}")
    print(f"wrote {history_path.relative_to(ROOT)}")
    print(f"wrote {public_report_path.relative_to(ROOT)}")
    print(f"wrote {index_path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect subreddit top posts with rdt-cli.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = load_config(args.config)
    report = collect(config)
    write_outputs(report, config)


if __name__ == "__main__":
    main()

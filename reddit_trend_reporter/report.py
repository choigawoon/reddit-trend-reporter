"""Send a compact snapshot to `claude -p` and write the analysis JSON back into
the collected report. The prompt + fallback are chosen by the config's
`profile` (see profiles.py); collection/snapshotting is shared across profiles."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .profiles import get_profile


def compact_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    subreddits = []
    for sub in data.get("subreddits", []):
        posts = []
        for p in sub.get("posts", []):
            comments = []
            discussion = p.get("discussion") or {}
            for comment in (discussion.get("comments") or [])[:12]:
                comments.append(
                    {
                        "id": comment.get("id"),
                        "author": comment.get("author"),
                        "score": comment.get("score"),
                        "body": (comment.get("body") or "")[:650],
                        "replies": [
                            {
                                "id": reply.get("id"),
                                "score": reply.get("score"),
                                "body": (reply.get("body") or "")[:300],
                            }
                            for reply in (comment.get("replies") or [])[:3]
                        ],
                    }
                )
            posts.append(
                {
                    "rank": p["rank"],
                    "id": p["id"],
                    "title": p["title"],
                    "score": p["score"],
                    "comments": p["comments"],
                    "flair": p.get("flair"),
                    "text": p.get("text", "")[:1000],
                    "discussion": {
                        "comments_collected": discussion.get("comments_collected", 0),
                        "comments": comments,
                    },
                }
            )
        sub_entry: dict[str, Any] = {"name": sub["name"], "posts": posts}
        trending_posts = (sub.get("trending") or {}).get("posts") or []
        if trending_posts:
            sub_entry["trending"] = [
                {
                    "rank": p.get("rank"),
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "score": p.get("score"),
                    "comments": p.get("comments"),
                }
                for p in trending_posts[:15]
            ]
        subreddits.append(sub_entry)
    return {"generated_at": data.get("generated_at"), "query": data.get("query"), "subreddits": subreddits}


def run_claude(snapshot: dict[str, Any], prompt: str, model: str | None) -> dict[str, Any]:
    full_prompt = prompt + "\nSNAPSHOT_JSON:\n" + json.dumps(snapshot, ensure_ascii=False)
    cmd = ["claude", "-p", full_prompt]
    if model:
        cmd.extend(["--model", model])
    raw = subprocess.check_output(cmd, text=True)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("Claude did not return JSON")
    return json.loads(raw[start : end + 1])


def _rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def sync_public_report(base_dir: Path, config: dict[str, Any], data: dict[str, Any]) -> None:
    """Mirror the analyzed snapshot into the dated public report referenced by
    index.latest, so the archive entry carries the same analysis."""
    index_path = base_dir / config.get("public_index", "public/data/index.json")
    if not index_path.exists():
        return
    try:
        index = json.loads(index_path.read_text())
    except json.JSONDecodeError:
        return
    latest = index.get("latest") or {}
    report_path = latest.get("path")
    if not report_path:
        return
    target = index_path.parent / report_path
    if target.exists():
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def run(
    config: dict[str, Any],
    base_dir: Path,
    *,
    model: str | None = None,
    allow_fallback: bool = False,
    input_path: Path | None = None,
) -> None:
    profile = get_profile(config.get("profile"))
    input_path = Path(input_path) if input_path else base_dir / config.get("output", "public/data/latest.json")
    data = json.loads(input_path.read_text())
    snapshot = compact_snapshot(data)
    try:
        analysis = run_claude(snapshot, profile["prompt"], model)
    except Exception:
        if not allow_fallback:
            raise
        analysis = profile["fallback"](snapshot)
    data["analysis"] = analysis
    data["profile"] = config.get("profile", "trend")
    input_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    sync_public_report(base_dir, config, data)
    print(f"updated {_rel(input_path, base_dir)} (profile: {data['profile']})")

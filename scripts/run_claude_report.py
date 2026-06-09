#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "public" / "data" / "latest.json"


PROMPT = """You are analyzing a Reddit trend snapshot.

Return only valid JSON with this shape:
{
  "headline": "short Korean headline",
  "summary": "Korean executive summary, 3-5 sentences",
  "top_topics": [
    {"name": "topic", "why_it_matters": "Korean explanation", "evidence_post_ids": ["..."]}
  ],
  "signals": [
    {"label": "signal", "detail": "Korean detail"}
  ],
  "watch_next": ["Korean item"],
  "risks_or_caveats": ["Korean caveat"]
}

Use only the provided snapshot. Do not invent external facts.
"""


def compact_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    subreddits = []
    for sub in data.get("subreddits", []):
        posts = []
        for p in sub.get("posts", []):
            posts.append(
                {
                    "rank": p["rank"],
                    "id": p["id"],
                    "title": p["title"],
                    "score": p["score"],
                    "comments": p["comments"],
                    "flair": p.get("flair"),
                    "text": p.get("text", "")[:700],
                }
            )
        subreddits.append({"name": sub["name"], "posts": posts})
    return {"generated_at": data.get("generated_at"), "query": data.get("query"), "subreddits": subreddits}


def run_claude(snapshot: dict[str, Any], model: str | None) -> dict[str, Any]:
    prompt = PROMPT + "\nSNAPSHOT_JSON:\n" + json.dumps(snapshot, ensure_ascii=False)
    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])
    raw = subprocess.check_output(cmd, text=True)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("Claude did not return JSON")
    return json.loads(raw[start : end + 1])


def fallback_analysis(snapshot: dict[str, Any]) -> dict[str, Any]:
    posts = []
    for sub in snapshot.get("subreddits", []):
        posts.extend(sub.get("posts", []))
    terms: dict[str, int] = {}
    for post in posts:
        title = (post.get("title") or "").lower()
        for key in ["ideogram", "anima", "comfy", "z-image", "ltx", "workflow", "censorship", "safety"]:
            if key in title:
                terms[key] = terms.get(key, 0) + 1
    top_terms = sorted(terms.items(), key=lambda item: item[1], reverse=True)[:5]
    leader = top_terms[0][0] if top_terms else "상위 게시글"
    return {
        "headline": f"이번 기간 핵심 화제는 {leader}",
        "summary": "Claude 분석을 실행하지 못해 스크립트 기반 요약을 사용했습니다. 상위 게시글의 제목, 점수, 댓글 수를 기준으로 반복 등장하는 키워드를 집계했습니다.",
        "top_topics": [
            {
                "name": name,
                "why_it_matters": f"상위 게시글 제목에서 {count}회 등장했습니다.",
                "evidence_post_ids": [p["id"] for p in posts if name in (p.get("title") or "").lower()][:5],
            }
            for name, count in top_terms
        ],
        "signals": [
            {"label": "top_posts", "detail": f"분석 대상 게시글 {len(posts)}개"},
            {"label": "keyword_fallback", "detail": "LLM 실패 시에도 웹 리포트가 비지 않도록 기본 집계를 제공합니다."},
        ],
        "watch_next": ["다음 실행에서 Claude 분석이 성공하는지 확인", "반복 등장 키워드의 댓글 증가 추세 확인"],
        "risks_or_caveats": ["이 fallback은 제목 기반 집계라 맥락 분석이 제한적입니다."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze latest Reddit snapshot with Claude headless.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model", default=None)
    parser.add_argument("--allow-fallback", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.input.read_text())
    snapshot = compact_snapshot(data)
    try:
        analysis = run_claude(snapshot, args.model)
    except Exception:
        if not args.allow_fallback:
            raise
        analysis = fallback_analysis(snapshot)
    data["analysis"] = analysis
    args.input.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"updated {args.input.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

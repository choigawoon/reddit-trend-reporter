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
  "community_voice": {
    "summary": "Korean qualitative summary of post bodies and comments",
    "sentiment": "positive | mixed | negative | polarized | unclear",
    "confidence": 0.0,
    "praise": [
      {"point": "what users praise", "evidence_post_ids": ["..."], "evidence_comment_ids": ["..."]}
    ],
    "complaints": [
      {"point": "what users complain about", "evidence_post_ids": ["..."], "evidence_comment_ids": ["..."]}
    ],
    "adoption_blockers": [
      {"point": "what blocks real use", "evidence_post_ids": ["..."], "evidence_comment_ids": ["..."]}
    ],
    "model_reputation_notes": [
      {"model": "model/tool name", "note": "qualitative reputation note", "evidence_post_ids": ["..."], "evidence_comment_ids": ["..."]}
    ],
    "representative_quotes": [
      {"kind": "praise | complaint | risk | use_case", "quote": "short excerpt under 25 words", "post_id": "...", "comment_id": "..."}
    ]
  },
  "commercial": {
    "verdict": "Go | Watch | Avoid",
    "confidence": 0.0,
    "summary": "Korean decision summary for commercial use",
    "opportunities": [
      {
        "title": "commercial opportunity",
        "customer": "who would pay or use it",
        "use_case": "what they can do with it",
        "monetization": "how this could become revenue or cost saving",
        "effort": "Low | Medium | High",
        "risk": "Low | Medium | High",
        "evidence_post_ids": ["..."]
      }
    ],
    "do_now": ["Korean action item"],
    "watch": ["Korean thing to monitor"],
    "avoid_or_review": ["Korean caveat, legal/IP/safety/brand concern"],
    "decision_notes": ["Korean note grounded in snapshot"]
  },
  "watch_next": ["Korean item"],
  "risks_or_caveats": ["Korean caveat"]
}

Use post bodies and comments when available. Commercial means practical business/product/content use. Be conservative about IP, licensing, safety-filter bypass, user privacy, and brand risk. Use only the provided snapshot. Do not invent external facts.
"""


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
        "community_voice": {
            "summary": "LLM 분석을 실행하지 못해 댓글 기반 정성평가를 제한적으로 제공합니다. 수집된 댓글이 있으면 UI에서 원문 근거를 확인하고, 다음 실행에서 Claude 분석을 재시도하세요.",
            "sentiment": "unclear",
            "confidence": 0.25,
            "praise": [],
            "complaints": [],
            "adoption_blockers": [],
            "model_reputation_notes": [],
            "representative_quotes": [],
        },
        "commercial": {
            "verdict": "Watch",
            "confidence": 0.45,
            "summary": "LLM 분석 실패로 보수적인 상업성 판단을 제공합니다. 반복 등장 키워드는 기회 신호지만, 실제 사용 전 모델 라이선스, IP 사용 가능성, 안전 필터 우회 여부를 별도로 확인해야 합니다.",
            "opportunities": [
                {
                    "title": f"{name} 기반 리서치 후보",
                    "customer": "AI 콘텐츠 제작자, 자동화 도구 사용자, 내부 리서치 팀",
                    "use_case": f"상위 게시글에서 반복 언급된 {name} 흐름을 제품/콘텐츠 아이디어 후보로 검토",
                    "monetization": "튜토리얼, 워크플로우 템플릿, 내부 생산성 자동화, 컨설팅 소재",
                    "effort": "Medium",
                    "risk": "Medium",
                    "evidence_post_ids": [p["id"] for p in posts if name in (p.get("title") or "").lower()][:5],
                }
                for name, _count in top_terms[:3]
            ],
            "do_now": ["상위 포스트별 라이선스/IP/상업 이용 조건을 확인", "반복 키워드별 1페이지 사업 가설로 정리"],
            "watch": ["다음 수집에서 같은 키워드가 유지되는지 확인", "댓글 수가 빠르게 늘어나는 글을 우선 검토"],
            "avoid_or_review": ["안전 필터 우회, 유명 IP 재현, 저작권 소재 활용은 상업 사용 전 검토 필요"],
            "decision_notes": ["fallback 분석은 제목 기반이라 상업성 판단의 신뢰도가 제한적입니다."],
        },
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
    sync_public_report(args.input, data)
    print(f"updated {args.input.relative_to(ROOT)}")


def sync_public_report(input_path: Path, data: dict[str, Any]) -> None:
    if input_path != DEFAULT_INPUT:
        return
    index_path = ROOT / "public" / "data" / "index.json"
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
    target = ROOT / "public" / "data" / report_path
    if target.exists():
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

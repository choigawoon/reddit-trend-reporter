"""Analysis profiles. Collection/normalization is shared across all profiles;
what differs is the Claude prompt + output schema + how the UI renders it.

Each profile is selected by the config's `profile` field. `trend` is the
original, fully-implemented behavior. `leaderboard` and `aigamedev` are
scaffolds: real prompts that emit at least `headline`/`summary` so the UI can
render something, with the richer schema to be fleshed out later.
"""
from __future__ import annotations

from typing import Any, Callable

# ---------------------------------------------------------------------------
# trend — established subreddit trend + community voice + commercial read
# ---------------------------------------------------------------------------

TREND_PROMPT = """You are analyzing a Reddit trend snapshot.

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

Use post bodies and comments when available. Commercial means practical business/product/content use. Be conservative about IP, licensing, safety-filter bypass, user privacy, and brand risk. Use only the provided snapshot. Do not invent external facts. Some subreddits include a `trending` list (rising posts gaining momentum); treat these as emerging signals distinct from the established top posts, and surface notable risers in `signals` and `watch_next`.
"""


def trend_fallback(snapshot: dict[str, Any]) -> dict[str, Any]:
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


# ---------------------------------------------------------------------------
# leaderboard (SCAFFOLD) — rank generative-AI models with evidence-backed tiers
# ---------------------------------------------------------------------------

LEADERBOARD_PROMPT = """You are building a generative-AI MODEL LEADERBOARD from a Reddit snapshot.

Goal: help a reader decide which model to actually try. Score must be defensible
from the snapshot, so prefer qualitative TIERS over fake-precise numbers, and
attach evidence (post/comment ids) to every claim.

Return only valid JSON with this shape:
{
  "headline": "short Korean headline naming the standout model(s)",
  "summary": "Korean executive summary, 3-5 sentences, on what's worth trying now",
  "models": [
    {
      "name": "model/tool name",
      "tier": "S | A | B | C",
      "one_liner": "Korean one-line verdict",
      "for_what": "Korean: what task it's best at",
      "mentions": 0,
      "sentiment": "positive | mixed | negative | polarized | unclear",
      "strengths": ["Korean strength"],
      "weaknesses": ["Korean weakness / blocker"],
      "try_if": "Korean: who should pick this up",
      "evidence_post_ids": ["..."],
      "evidence_comment_ids": ["..."]
    }
  ],
  "methodology": "Korean note on how tiers were derived from the snapshot (mention volume, sentiment, upvotes) and its limits",
  "risks_or_caveats": ["Korean caveat"]
}

Rank only models actually evidenced in the snapshot. Do not invent models or
facts. Be explicit about uncertainty. Use only the provided snapshot.
"""


def leaderboard_fallback(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "headline": "모델 리더보드 (스캐폴드)",
        "summary": "Claude 분석을 실행하지 못했거나 아직 채워지지 않은 프로파일입니다. config/leaderboard.json의 대상 서브레딧을 정하고 `reddit-report pipeline --config config/leaderboard.json`을 실행하면 모델별 티어와 근거가 채워집니다.",
        "models": [],
        "methodology": "스캐폴드 상태 — 스코어링 방식(언급량·정서·upvote 가중, 정성 티어 + 근거 id)을 확정한 뒤 구현 예정.",
        "risks_or_caveats": ["아직 분석 내용이 없습니다."],
    }


# ---------------------------------------------------------------------------
# aigamedev (SCAFFOLD) — keyword / interest / hot-workflow market research
# ---------------------------------------------------------------------------

AIGAMEDEV_PROMPT = """You are doing MARKET/INTEREST RESEARCH for AI game development from a Reddit snapshot.

Goal: surface what people are genuinely excited about — hot workflows, assets,
tools, and recurring keywords — for a creator scouting ideas.

Return only valid JSON with this shape:
{
  "headline": "short Korean headline",
  "summary": "Korean executive summary, 3-5 sentences",
  "keywords": [
    {"term": "keyword", "count": 0, "why": "Korean why it's notable", "evidence_post_ids": ["..."]}
  ],
  "hot_workflows": [
    {"name": "workflow / asset / technique", "what": "Korean: what it is and why people love it", "evidence_post_ids": ["..."], "evidence_comment_ids": ["..."]}
  ],
  "interests": [
    {"theme": "interest cluster", "detail": "Korean detail", "evidence_post_ids": ["..."]}
  ],
  "watch_next": ["Korean item"],
  "risks_or_caveats": ["Korean caveat"]
}

Focus on genuine enthusiasm signals (high engagement, repeated asks, shared
workflows). Use only the provided snapshot. Do not invent external facts.
"""


def aigamedev_fallback(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "headline": "AI 게임개발 리서치 (스캐폴드)",
        "summary": "Claude 분석을 실행하지 못했거나 아직 채워지지 않은 프로파일입니다. config/aigamedev.json의 대상(예: aigamedev)을 확인하고 `reddit-report pipeline --config config/aigamedev.json`을 실행하면 키워드·열광 workflow·관심사가 채워집니다.",
        "keywords": [],
        "hot_workflows": [],
        "interests": [],
        "watch_next": [],
        "risks_or_caveats": ["아직 분석 내용이 없습니다."],
    }


# ---------------------------------------------------------------------------

Profile = dict[str, Any]

PROFILES: dict[str, Profile] = {
    "trend": {
        "label": "Trend",
        "kind": "trend",
        "prompt": TREND_PROMPT,
        "fallback": trend_fallback,
    },
    "leaderboard": {
        "label": "Model Leaderboard",
        "kind": "leaderboard",
        "prompt": LEADERBOARD_PROMPT,
        "fallback": leaderboard_fallback,
    },
    "aigamedev": {
        "label": "Game Dev Research",
        "kind": "aigamedev",
        "prompt": AIGAMEDEV_PROMPT,
        "fallback": aigamedev_fallback,
    },
}

DEFAULT_PROFILE = "trend"


def get_profile(name: str | None) -> Profile:
    return PROFILES.get(name or DEFAULT_PROFILE, PROFILES[DEFAULT_PROFILE])

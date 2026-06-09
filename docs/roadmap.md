# Roadmap

## Phase 1: Comment-Enriched Collection

Goal: read what people are actually saying, not only post titles and scores.

Implementation plan:

1. Add config fields:
   - `read_top_posts`: number of top posts to read, e.g. `10`.
   - `max_comments_per_post`: e.g. `30`.
   - `comment_sort`: `top` or `best`.
2. Add `scripts/enrich_comments.py` or extend `collect_reddit.py`.
3. For each selected post, call:

   ```bash
   rdt read <post_id> --json
   ```

4. Normalize:
   - post body
   - top-level comments
   - nested replies up to a small depth
   - comment score
   - comment author
   - comment id
5. Store compact excerpts in `public/data/latest.json`.

## Phase 2: Qualitative Sentiment

Goal: identify how the community feels.

LLM output should include:

- praised capabilities
- pain points
- adoption blockers
- repeated complaints
- surprising use cases
- buying/usage intent signals
- controversy and polarization

## Phase 3: Model Reputation Knowledge Base

Goal: maintain long-lived qualitative notes per generative AI model/tool.

Write/update `knowledge/models/<model-slug>.json` with:

- aliases
- category
- current sentiment
- strengths
- weaknesses
- commercial readiness
- IP/licensing/safety concerns
- evidence report IDs
- observed over time
- last updated date

Start with:

- `ideogram-4.json`
- `anima.json`
- `z-image.json`
- `ltx-2-3.json`
- `comfyui.json`

## Phase 4: UI for Model Knowledge

Add a `Models` tab:

- model list
- current reputation score
- strengths/weaknesses
- commercial readiness
- recent supporting reports
- history timeline

## Phase 5: Multi-Source Collection

Potential future collectors:

- Hacker News
- YouTube comments
- X/Twitter search
- Discord exports
- GitHub issues/discussions

Keep collector outputs compatible with the same report schema.

#!/usr/bin/env bash
# Bootstrap every dependency reddit-trend-reporter needs on a fresh machine.
# Idempotent: safe to re-run. Does NOT touch Reddit/Claude credentials.
set -euo pipefail

cd "$(dirname "$0")/.."

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

say "Node packages (vite/react)"
npm install

say "uv (Python tool runner)"
if command -v uv >/dev/null 2>&1; then
  echo "uv present: $(uv --version)"
else
  echo "installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # make uv visible for the rest of this script without a new shell
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

say "rdt-cli (Reddit collector)"
if command -v rdt >/dev/null 2>&1; then
  echo "rdt present: $(command -v rdt)"
else
  uv tool install rdt-cli
  echo "Note: ensure '$HOME/.local/bin' is on your PATH (uv tool install warns if not)."
fi

say "Claude CLI (LLM report step) — checked, not installed"
if command -v claude >/dev/null 2>&1; then
  echo "claude present: $(claude --version 2>/dev/null || echo 'unknown version')"
else
  echo "WARN: claude not found. Install + sign in before running without --skip-llm."
  echo "      See https://docs.claude.com/claude-code  (or run pipeline with --skip-llm)."
fi

say "Reddit auth status"
rdt status --json 2>/dev/null || cat <<'EOF'
WARN: rdt is not authenticated yet.
If Reddit is logged into a non-default Chrome profile, create the credential
file manually or point rdt-cli at that profile before collecting.
EOF

say "Done"
echo "Next: npm run pipeline            (full run)"
echo "      npm run pipeline -- --skip-llm   (no Claude call)"

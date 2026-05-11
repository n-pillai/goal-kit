#!/usr/bin/env bash
# Bash variant of run_goal_step.py — kept in parity with the Python version.
# Both share the same contract: one-shot iteration runner that reads GOAL.md,
# invokes `claude -p`, dual-writes the JSON to .goal-runs/<ts>.json and
# .goal-last-run.json, and respects the iteration cap.
#
# Use this on macOS/Linux when you'd rather not depend on Python.
# The Python version is canonical; if these diverge, prefer the .py.
#
# NOTE: This bash variant enforces only the iteration cap (env-var
# GOAL_MAX_ITERATIONS, default 12). For full USD/token budget enforcement
# driven by a ## Budget section in GOAL.md, use run_goal_step.py — bash math
# on archived JSONs would require either jq or a Python helper, neither of
# which is worth the dependency for the simpler runner.
set -euo pipefail

PROJECT_DIR="${1:-$PWD}"
DIRECTIVE="${2:-}"
cd "$PROJECT_DIR"

# --- Status check ---
if [[ ! -f GOAL.md ]]; then
  echo "[goal-step] $PROJECT_DIR: no GOAL.md, skipping."
  exit 0
fi

STATUS=$(grep -E '^\*\*Status:\*\*' GOAL.md | head -1 \
  | sed -E 's/.*Status:\*\* *//' \
  | tr '[:upper:]' '[:lower:]' \
  | tr -d '[:space:]' \
  || true)

if [[ "$STATUS" != "active" ]]; then
  echo "[goal-step] $PROJECT_DIR: status='$STATUS', skipping."
  exit 0
fi

# --- Iteration cap (defense-in-depth; parity with Python) ---
# Source of truth: file count in .goal-runs/ (matches Python). Falls back to
# progress-log-line count if .goal-runs/ doesn't exist yet (first run, or
# legacy goal predating the archive).
MAX_ITER="${GOAL_MAX_ITERATIONS:-12}"
if [[ -d .goal-runs ]]; then
  ITER_COUNT=$(find .goal-runs -maxdepth 1 -name '*.json' -type f 2>/dev/null | wc -l | tr -d ' ')
else
  ITER_COUNT=$(grep -cE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T' GOAL.md || true)
fi
if [[ "$ITER_COUNT" -ge "$MAX_ITER" ]]; then
  echo "[goal-step] $PROJECT_DIR: $ITER_COUNT iterations already logged " \
       "(cap=$MAX_ITER), skipping. Override with GOAL_MAX_ITERATIONS env var."
  exit 0
fi

# --- claude on PATH ---
if ! command -v claude >/dev/null 2>&1; then
  echo "[goal-step] ERROR: \`claude\` CLI not found on PATH." >&2
  exit 2
fi

# --- Build prompt (kept aligned with Python's STEP_PROMPT) ---
PROMPT='Read GOAL.md. If Status is not "active", stop. Otherwise take EXACTLY ONE concrete step toward the Objective. Run the Validation commands (or the most relevant ones). Append ONE progress log entry at the top of the Progress log section, format: "<ISO 8601 UTC timestamp> | <action> | <validation outcome> | <planned next step>". If any Stop condition is met, change Status to "done" and append a final entry. If you cannot make progress (e.g. blocked on missing info), append an entry explaining the blocker and stop -- do NOT change Non-goals. Be concise.

**Sourcing discipline (every iteration):** when stating a factual claim alongside a citation, the cited source must directly support THAT specific fact. Do NOT pad cited statements with adjacent details imported from your training that the source does not explicitly state -- those are confabulation, not sourced claims, and they undermine the trust model of the loop. If a detail is not in the source you are citing, either drop it or label it explicitly as "opinion" or "inferred".'

if [[ -n "$DIRECTIVE" ]]; then
  PROMPT="$PROMPT

**Directive for THIS iteration (overrides the agent's own choice of next step):** $DIRECTIVE"
  echo "[goal-step] directive: $DIRECTIVE"
fi

# --- Run claude, dual-write the result ---
mkdir -p .goal-runs
TS=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
ARCHIVE_PATH=".goal-runs/$TS.json"
LAST_PATH=".goal-last-run.json"

echo "[goal-step] $PROJECT_DIR: running claude -p (directive: ${DIRECTIVE:-none})"
# bypassPermissions: parity with Python. Tool use is bounded by Non-goals in
# GOAL.md, not by interactive prompts.
claude -p "$PROMPT" \
  --output-format json \
  --permission-mode bypassPermissions \
  > "$ARCHIVE_PATH"

cp "$ARCHIVE_PATH" "$LAST_PATH"

echo "[goal-step] step complete; archive -> $ARCHIVE_PATH"
echo "[goal-step] (also written to $LAST_PATH for latest-pointer reads)"

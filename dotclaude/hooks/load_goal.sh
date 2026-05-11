#!/usr/bin/env bash
# SessionStart hook (bash variant). Same behavior as load_goal.py.
# Use this if you don't want a python3 dependency.
set -euo pipefail

GOAL_FILE="${CLAUDE_PROJECT_DIR:-$PWD}/GOAL.md"
[[ -f "$GOAL_FILE" ]] || exit 0

STATUS=$(grep -E '^\*\*Status:\*\*' "$GOAL_FILE" | head -1 \
  | sed -E 's/.*Status:\*\* *//' \
  | tr '[:upper:]' '[:lower:]' \
  | tr -d '[:space:]' \
  || true)

[[ "$STATUS" == "active" ]] || exit 0

cat <<'EOF'
## Active long-horizon goal (loaded from GOAL.md)

You have a persistent objective. Before responding to the user, read the
goal below. When asked to make progress, take ONE concrete step, run the
Validation commands, append a Progress log entry, and stop. Never modify
anything listed in Non-goals.

If the user is asking about something unrelated, answer them; do not force
the goal into every response.

---

EOF
cat "$GOAL_FILE"
echo

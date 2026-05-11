#!/usr/bin/env python3
"""SessionStart hook: inject GOAL.md into the new session when status is `active`.

Why a hook:
  Codex's /goal "survives session breaks" because the runtime injects the goal
  at every continuation. We get the same effect by reading GOAL.md on
  SessionStart and printing it to stdout — Claude Code prepends hook stdout
  to the session context.

Behavior:
  - No GOAL.md           -> exit silently (0).
  - Status != active     -> exit silently (0).
  - Status == active     -> print a header + the full GOAL.md to stdout.

Exit codes:
  0  always (a SessionStart hook should never block session start).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _read_status(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**Status:**"):
            return stripped.replace("**Status:**", "").strip().lower()
    return "unknown"


def main() -> int:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    goal_path = Path(project_dir) / "GOAL.md"
    if not goal_path.exists():
        return 0

    try:
        text = goal_path.read_text(encoding="utf-8")
    except OSError:
        return 0

    if _read_status(text) != "active":
        return 0

    sys.stdout.write(
        "## Active long-horizon goal (loaded from GOAL.md)\n\n"
        "You have a persistent objective. Before responding to the user, "
        "read the goal below. When asked to make progress, take ONE concrete "
        "step, run the Validation commands, append a Progress log entry, and "
        "stop. Never modify anything listed in Non-goals.\n\n"
        "If the user is asking about something unrelated, answer them; do not "
        "force the goal into every response.\n\n"
        "---\n\n"
    )
    sys.stdout.write(text)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

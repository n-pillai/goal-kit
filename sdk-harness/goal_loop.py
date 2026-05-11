#!/usr/bin/env python3
"""Goal loop harness — Agent SDK version of run_goal_step.py.

This is a STUB. The structure is real (status check, budget tracking,
iteration cap, graceful halt). The model call is commented out — wire it
in once you've installed claude-agent-sdk and decided on options.

Why this exists: see ./README.md.
"""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# from claude_agent_sdk import query, ClaudeAgentOptions  # noqa: F401  (uncomment after install)


# ---------------------------------------------------------------------------
# Stub-only defaults. The real implementation should read GOAL.md's
# ## Budget section the same way scripts/run_goal_step.py does — see
# parse_budget() / compute_usage() / check_budget() in that file. Copy
# those helpers when you wire up the real query() call below. These
# constants exist only so the loop has SOMETHING to terminate on while
# you're scaffolding.
# ---------------------------------------------------------------------------
STUB_MAX_ITERATIONS = 50      # only used while the SDK call is commented out
STUB_MAX_TOKENS = 1_000_000   # only used while the SDK call is commented out
ITER_PROMPT = (
    "Read GOAL.md. Take ONE concrete step toward the Objective. "
    "Run the Validation commands. Append ONE progress log entry at the top "
    "of the Progress log section. If a Stop condition is met OR you cannot "
    "make progress, set Status to 'done' (or 'paused' with a blocker note) "
    "and stop. Never modify Non-goals."
    "\n\n"
    "Sourcing discipline: when citing a source for a factual claim, the "
    "source must directly support THAT specific fact. Do not append adjacent "
    "details from training that aren't in the source -- drop them or label "
    "as opinion."
)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------
@dataclass
class GoalState:
    status: str
    text: str


def read_goal(goal_path: Path) -> GoalState | None:
    if not goal_path.exists():
        return None
    text = goal_path.read_text(encoding="utf-8")
    status = "unknown"
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("**Status:**"):
            status = s.replace("**Status:**", "").strip().lower()
            break
    return GoalState(status=status, text=text)


# ---------------------------------------------------------------------------
# The loop.
# ---------------------------------------------------------------------------
async def run(project_dir: Path) -> int:
    goal_path = project_dir / "GOAL.md"
    tokens_used = 0

    for i in range(STUB_MAX_ITERATIONS):
        state = read_goal(goal_path)
        if state is None:
            print(f"[{i}] no GOAL.md at {goal_path}; halting.")
            return 0
        if state.status != "active":
            print(f"[{i}] status='{state.status}'; halting.")
            return 0
        if tokens_used >= STUB_MAX_TOKENS:
            print(f"[{i}] stub token budget exhausted ({tokens_used}); halting.")
            return 0

        print(f"[{i}] running iteration. status=active, tokens_used={tokens_used}")

        # ----- TODO: replace this stub with a real SDK call -----
        # async for msg in query(
        #     prompt=ITER_PROMPT,
        #     options=ClaudeAgentOptions(cwd=str(project_dir), permission_mode="acceptEdits"),
        # ):
        #     # Inspect msg for tool calls, results, errors.
        #     if getattr(msg, "usage", None):
        #         tokens_used += msg.usage.total_tokens
        # ---------------------------------------------------------
        #
        # PARITY NOTE: when wiring this up, archive the run JSON to match the
        # script-based loop. The convention is:
        #   1. Write the full result to .goal-runs/<ISO timestamp>.json
        #      (never-overwritten, per-iteration archive for visibility).
        #   2. Also write to .goal-last-run.json (latest pointer; backward
        #      compat with anything that reads the original path).
        # See scripts/run_goal_step.py for the reference implementation.

        await asyncio.sleep(1)  # remove once the real call is wired in

    print(f"[{STUB_MAX_ITERATIONS}] stub iteration cap reached; halting.")
    return 0


def main() -> int:
    project_dir = Path(sys.argv[1] if len(sys.argv) > 1 else os.getcwd()).resolve()
    if not project_dir.is_dir():
        print(f"not a directory: {project_dir}", file=sys.stderr)
        return 2
    return asyncio.run(run(project_dir))


if __name__ == "__main__":
    raise SystemExit(main())

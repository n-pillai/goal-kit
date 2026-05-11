#!/usr/bin/env python3
"""Run one iteration of the goal loop.

Usage:
    python run_goal_step.py [project_dir]

Behavior:
    - No GOAL.md, or status != active -> exit 0 (silent no-op).
    - Otherwise: invoke `claude -p "<step prompt>"` non-interactively in
      project_dir. Claude is expected to take ONE concrete step, run
      validation, append a progress log entry, and (if a Stop condition
      fires) flip Status to `done`.

Wire this into:
    - cron / launchd / Windows Task Scheduler  (every 15 min is a good start)
    - Cowork: `mcp__scheduled-tasks__create_scheduled_task`
    - GitHub Actions on a schedule trigger (set CLAUDE_PROJECT_DIR)

This script is intentionally dumb. Real orchestration lives in Claude itself
(it reads GOAL.md and decides what to do). Keep this file boring.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

STEP_PROMPT = (
    "Read GOAL.md. If Status is not 'active', stop. "
    "Otherwise: take EXACTLY ONE concrete step toward the Objective. "
    "Run the Validation commands (or the most relevant ones). "
    "Append ONE progress log entry at the top of the Progress log section, "
    "format: '<ISO 8601 UTC timestamp> | <action> | <validation outcome> | <planned next step>'. "
    "If any Stop condition is met, change Status to 'done' and append a final entry. "
    "If you cannot make progress (e.g. blocked on missing info), append an entry "
    "explaining the blocker and stop -- do NOT change Non-goals. Be concise."
    "\n\n"
    "**Sourcing discipline (every iteration):** when stating a factual claim "
    "alongside a citation, the cited source must directly support THAT specific "
    "fact. Do NOT pad cited statements with adjacent details imported from your "
    "training that the source doesn't explicitly state -- those are "
    "confabulation, not sourced claims, and they undermine the trust model of "
    "the loop. If a detail isn't in the source you're citing, either drop it "
    "or label it explicitly as 'opinion' or 'inferred'."
)


def read_status(goal_path: Path) -> str:
    if not goal_path.exists():
        return "missing"
    try:
        for line in goal_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("**Status:**"):
                return s.replace("**Status:**", "").strip().lower()
    except OSError:
        return "unreadable"
    return "unknown"


# ---------------------------------------------------------------------------
# Budget enforcement.
#
# GOAL.md may contain a ## Budget section with any of:
#     - max_usd: 20.00
#     - max_iterations: 12
#     - max_output_tokens: 500000
#     - max_input_tokens: 5000000
#
# Omit any field to leave that dimension uncapped. The script reads all
# .goal-runs/*.json each run to compute cumulative usage (no separate state
# file, no drift). Hard-stops at the cap; soft-stops by injecting a budget
# status note into the iteration prompt so the agent can self-flip Status.
#
# GOAL_MAX_ITERATIONS env var still works as a fallback default if the goal
# does not specify max_iterations.
# ---------------------------------------------------------------------------


def parse_budget(goal_path: Path) -> dict:
    """Extract budget values from GOAL.md's ## Budget section."""
    if not goal_path.exists():
        return {}
    try:
        body = goal_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    budget: dict = {}
    in_budget = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_budget = stripped.lower() == "## budget"
            continue
        if not in_budget:
            continue
        m = re.match(r"^\s*-\s*(\w+)\s*:\s*([\d.]+)\s*$", line)
        if not m:
            continue
        key, val = m.group(1).lower(), m.group(2)
        try:
            budget[key] = float(val) if "." in val else int(val)
        except ValueError:
            pass
    return budget


def compute_usage(runs_dir: Path) -> dict:
    """Sum cost / tokens / iterations across all archived runs."""
    usage = {
        "total_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "iterations": 0,
    }
    if not runs_dir.is_dir():
        return usage
    for f in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        usage["total_usd"] += float(data.get("total_cost_usd") or 0)
        u = data.get("usage") or {}
        if isinstance(u, dict):
            usage["input_tokens"] += int(u.get("input_tokens") or 0)
            usage["input_tokens"] += int(u.get("cache_creation_input_tokens") or 0)
            usage["output_tokens"] += int(u.get("output_tokens") or 0)
        usage["iterations"] += 1
    return usage


def check_budget(budget: dict, usage: dict) -> str:
    """Return empty string if within budget, else a reason string."""
    if "max_usd" in budget and usage["total_usd"] >= budget["max_usd"]:
        return f"USD cap reached: ${usage['total_usd']:.2f} of ${budget['max_usd']:.2f}"
    if "max_iterations" in budget and usage["iterations"] >= budget["max_iterations"]:
        return (f"iteration cap reached: {usage['iterations']} of "
                f"{budget['max_iterations']}")
    if "max_output_tokens" in budget and usage["output_tokens"] >= budget["max_output_tokens"]:
        return (f"output token cap reached: {usage['output_tokens']:,} of "
                f"{budget['max_output_tokens']:,}")
    if "max_input_tokens" in budget and usage["input_tokens"] >= budget["max_input_tokens"]:
        return (f"input token cap reached: {usage['input_tokens']:,} of "
                f"{budget['max_input_tokens']:,}")
    return ""


def budget_prompt_note(budget: dict, usage: dict) -> str:
    """Return a status block to prepend to the iteration prompt."""
    if not budget:
        return ""
    lines = ["**Budget status before this iteration:**"]
    if "max_usd" in budget:
        pct = (usage["total_usd"] / budget["max_usd"] * 100) if budget["max_usd"] else 0
        lines.append(f"- USD: ${usage['total_usd']:.2f} of ${budget['max_usd']:.2f} ({pct:.0f}%)")
    if "max_iterations" in budget:
        lines.append(f"- Iterations: {usage['iterations']} of {budget['max_iterations']}")
    if "max_output_tokens" in budget:
        pct = (usage["output_tokens"] / budget["max_output_tokens"] * 100) if budget["max_output_tokens"] else 0
        lines.append(f"- Output tokens: {usage['output_tokens']:,} of "
                     f"{budget['max_output_tokens']:,} ({pct:.0f}%)")
    if "max_input_tokens" in budget:
        pct = (usage["input_tokens"] / budget["max_input_tokens"] * 100) if budget["max_input_tokens"] else 0
        lines.append(f"- Input tokens: {usage['input_tokens']:,} of "
                     f"{budget['max_input_tokens']:,} ({pct:.0f}%)")
    lines.append("")
    lines.append(
        "If usage is at or above 80% of any cap, consider flipping Status to "
        "'done' (or 'paused' with a summary) instead of starting more work. "
        "The runner will hard-stop at 100% of any cap regardless."
    )
    return "\n\n" + "\n".join(lines)


def main() -> int:
    # argv[1] = project_dir (default: cwd)
    # argv[2:] = optional one-shot directive appended to STEP_PROMPT for THIS iteration
    args = sys.argv[1:]
    project_dir = Path(args[0] if args else os.getcwd()).resolve()
    directive = " ".join(args[1:]).strip() if len(args) > 1 else ""
    goal_path = project_dir / "GOAL.md"

    status = read_status(goal_path)
    if status != "active":
        print(f"[goal-step] {project_dir}: status='{status}', skipping.")
        return 0

    # Budget: read from GOAL.md, sum from .goal-runs/, enforce.
    budget = parse_budget(goal_path)
    if "max_iterations" not in budget:
        budget["max_iterations"] = int(os.environ.get("GOAL_MAX_ITERATIONS", "12"))
    runs_dir = project_dir / ".goal-runs"
    usage = compute_usage(runs_dir)
    reason = check_budget(budget, usage)
    if reason:
        print(f"[goal-step] {project_dir}: {reason}, skipping.")
        return 0
    print(f"[goal-step] budget so far: ${usage['total_usd']:.2f} USD, "
          f"{usage['iterations']} iters, {usage['output_tokens']:,} out / "
          f"{usage['input_tokens']:,} in tokens")

    claude = shutil.which("claude")
    if claude is None:
        print("[goal-step] ERROR: `claude` CLI not found on PATH.", file=sys.stderr)
        return 2

    prompt = STEP_PROMPT + budget_prompt_note(budget, usage)
    if directive:
        prompt += (
            "\n\n**Directive for THIS iteration (overrides the agent's own choice "
            f"of next step):** {directive}"
        )
        print(f"[goal-step] directive: {directive}")

    cmd = [
        claude, "-p", prompt,
        "--output-format", "json",
        # bypassPermissions: this is an autonomous goal loop. Tool use is
        # bounded by the Non-goals section in GOAL.md, not by interactive
        # prompts. For a tighter setup, replace with:
        #   "--allowed-tools", "Read,Write,Edit,WebSearch,WebFetch,Bash"
        "--permission-mode", "bypassPermissions",
    ]
    print(f"[goal-step] {project_dir}: running `{shlex.join(cmd)}`")
    # encoding="utf-8" + errors="replace": claude's output contains characters
    # outside the Windows default code page (cp1252) -- em-dashes, smart quotes,
    # arrows. Without this, subprocess crashes on Windows reading stdout.
    result = subprocess.run(
        cmd,
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Dual-write for visibility: timestamped archive in .goal-runs/ for
    # post-hoc analysis (cost-per-iteration, tool-call traces), plus
    # .goal-last-run.json as a "latest pointer" for backward compatibility.
    runs_dir = project_dir / ".goal-runs"
    runs_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    archive_path = runs_dir / f"{ts}.json"
    last_path = project_dir / ".goal-last-run.json"
    content = result.stdout or ""
    archive_path.write_text(content, encoding="utf-8")
    last_path.write_text(content, encoding="utf-8")

    if result.returncode != 0:
        print(f"[goal-step] claude exited {result.returncode}", file=sys.stderr)
        sys.stderr.write(result.stderr or "")
        return result.returncode

    print(f"[goal-step] step complete; archive -> {archive_path}")
    print(f"[goal-step] (also written to {last_path} for latest-pointer reads)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

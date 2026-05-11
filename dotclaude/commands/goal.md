---
description: Set or replace the long-horizon goal stored in GOAL.md
argument-hint: <objective>
---

You are managing a persistent goal for this project, stored in `GOAL.md` at the
project root. The user wants to set a new goal:

**$ARGUMENTS**

Do this in order:

1. Read the current `GOAL.md`. If it exists with `Status: active`, warn the user
   that they're replacing an active goal and ask them to confirm before
   overwriting (offer to run `/goal-clear` first to archive it).

2. Draft a new GOAL.md with these sections filled in:
   - **Status:** `active`
   - **Objective:** $ARGUMENTS (rewrite for clarity if needed; keep the user's intent).
   - **Non-goals:** propose 2–4 concrete boundaries based on the objective —
     files/areas/behaviors that should NOT change. If you can't propose any
     confidently, leave a clear `<!-- TODO: confirm with user -->` and ask.
   - **Validation:** propose 2–4 concrete checks (commands to run, signals to
     watch). Prefer commands that already exist in this repo (look for
     package.json scripts, Makefile targets, pytest config, etc.). If unclear,
     leave a TODO and ask.
     - **If the goal involves factual claims, research, or any output that
       cites sources,** ALWAYS include this Validation rule verbatim:
       "Every cited source must directly support the specific claim it's
       attached to. No adjacent details from training that aren't in the
       source — drop them, or label as opinion." This catches the failure
       mode where the agent appends plausible but unsourced details to a
       real citation (e.g. citing a real product page but inventing material
       composition that isn't on it).
   - **Budget:** propose sensible defaults the runner will enforce as
     hard caps and inject into every iteration's prompt:
       - `max_usd`: a reasonable dollar cap based on goal scope. For
         research/document goals expect ~$0.50–$2 per iteration; for
         code-touching goals possibly higher. Default suggestion: $20.
       - `max_iterations`: default 12 (matches the runner fallback).
       - `max_output_tokens` and `max_input_tokens`: optional. Only include
         if the user has a specific token-spend concern. Otherwise omit
         (leave those dimensions uncapped).
     If the user explicitly doesn't want budget enforcement, leave the
     Budget section out entirely — the runner falls back to iteration cap
     only via the env var.
   - **Stop conditions:** propose 2–3 (e.g., "all validation checks green",
     "PR opened against main", "10 iterations without a green validation",
     "approaching any Budget cap").
   - **Progress log:** reset to `_(empty)_`.

3. Show the proposed GOAL.md to the user as a single fenced markdown block
   and ask: "Confirm to write this, or edit first?"

4. After they confirm, write `GOAL.md` and tell them: "Goal active. Next
   session will auto-load it. Run `/goal-status` any time, or schedule
   `scripts/run_goal_step.py` to make progress automatically."

Do NOT start working on the goal during this command — `/goal` is for
defining the objective, not pursuing it.

# sdk-harness — graduate from "scheduled task" to "real loop"

The scheduled-task approach in `scripts/run_goal_step.py` is fine for most
goals: every 15 minutes Claude wakes up, reads `GOAL.md`, takes one step,
goes back to sleep. Boring is good.

Graduate to this harness when you want any of:

- **Sub-15-minute iteration cadence** — back-to-back steps with no idle gap.
- **Hard token budget** — stop after N tokens, not after N iterations.
- **Programmatic stop detection** — parse Claude's output for "DONE" / errors
  and react, instead of relying on Claude self-flagging Status=done.
- **Custom validation gates** — run your own pytest/lint/build between steps
  and feed the results back as part of the next prompt.
- **Multi-goal orchestration** — one harness driving N goals across N repos.

When you wire this up, keep parity with the script-based loop on three
things: the **archive convention** (write each run's JSON to
`.goal-runs/<ISO timestamp>.json` AND to `.goal-last-run.json`), the
**sourcing-discipline clause** in the iteration prompt, and **budget
enforcement** (read GOAL.md's `## Budget` section, sum cumulative usage
from `.goal-runs/`, hard-stop at caps, and inject the budget status into
the iteration prompt for soft-stop self-flipping).

The reference implementation of all three lives in `scripts/run_goal_step.py`
(`parse_budget`, `compute_usage`, `check_budget`, `budget_prompt_note`, and
the dual-write block in `main()`). The harness here is a **stub** — it does
not implement any of the three yet. It uses hardcoded `STUB_MAX_ITERATIONS`
and `STUB_MAX_TOKENS` placeholders that you should replace with real Budget
parsing copied from the script when you wire up the actual SDK `query()`
call. Until you do that, this harness will run a fixed number of dummy
iterations regardless of what GOAL.md says.

This file is a STUB. It boots, reads `GOAL.md`, and structures the loop, but
the actual `query()` call is commented out so you can wire in the model and
options that fit your subscription. Install the SDK first:

```
pip install claude-agent-sdk
export ANTHROPIC_API_KEY=...
python goal_loop.py /path/to/project
```

The Claude Agent SDK docs cover `query()`, `ClaudeAgentOptions`, session
resumption, and subagent spawning — those are the building blocks you'd use
to make this harness production-grade.

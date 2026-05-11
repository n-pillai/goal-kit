# goal-kit — a `/goal` for Claude Code & Cowork

A portable starter kit that gives Claude Code (and Cowork) the same long-horizon
behavior as Codex CLI's `/goal`: a durable objective that survives session breaks,
five lifecycle commands (set / status / pause / resume / clear), an auto-loaded
goal context, and a continuation loop.

## What's in here

```
goal-kit/
├── README.md                  ← you are here
├── GOAL.md                    ← the goal template (copy to your repo root)
├── dotclaude/                 ← rename to ".claude/" after copying into a project
│   ├── settings.json          ← wires up the SessionStart hook
│   ├── hooks/
│   │   ├── load_goal.py       ← portable Python hook (default)
│   │   └── load_goal.sh       ← bash alternative
│   └── commands/
│       ├── goal.md            ← /goal <objective>
│       ├── goal-status.md     ← /goal-status
│       ├── goal-pause.md      ← /goal-pause
│       ├── goal-resume.md     ← /goal-resume
│       └── goal-clear.md      ← /goal-clear
├── scripts/
│   ├── run_goal_step.py       ← one iteration of the loop (call from cron/scheduler)
│   └── run_goal_step.sh       ← bash variant (parity-maintained with .py)
└── sdk-harness/
    ├── README.md              ← when/why to graduate to this
    └── goal_loop.py           ← Agent SDK stub for tighter continuation
```

After the first run, two more paths appear at the project root:

```
├── .goal-runs/                ← per-iteration JSON archive (one file per run, never overwritten)
│   ├── 2026-05-09T05-19-00Z.json
│   ├── 2026-05-09T05-30-00Z.json
│   └── ...
└── .goal-last-run.json        ← latest pointer (overwritten each run; for backward-compat reads)
```

Both are auto-created. Plus `goal-archive/` will appear if you ever run
`/goal-clear` (it stores archived GOAL.md snapshots from past goals).
Suggested `.gitignore` entries if you don't want any of this in version
control:

```
.goal-runs/
.goal-last-run.json
goal-archive/
__pycache__/
*.pyc
```


> **Note on `dotclaude/`:** Claude Code expects this folder to be named
> `.claude/` (with the leading dot). The kit ships it as `dotclaude/` because
> some sandboxed environments block writing to `.claude` paths. After copying
> into your project, rename it: `mv dotclaude .claude` (or
> `Rename-Item dotclaude .claude` on Windows).

## Install into a project

1. Copy `GOAL.md` and `dotclaude/` to your project root.
2. Rename `dotclaude/` to `.claude/`.
3. Copy `scripts/` somewhere convenient (or reference it from cron by absolute path).
4. Open a new Claude Code session in that project. The five `/goal*` commands
   will be available, and the `SessionStart` hook will auto-inject the goal
   on every new session whenever its status is `active`.

## Daily use

```
/goal Migrate the api/v1 client to v2 across all callers
# Claude fills in Non-goals, Validation, Stop conditions, then asks you to confirm.

/goal-status      # what's the current goal? recent progress?
/goal-pause       # stop the loop, keep state
/goal-resume      # pick back up from the latest progress entry
/goal-clear       # archive current goal and reset to template
```

## Running the loop

**Option A — Scheduled task (recommended to start).** Set up a cron job (or a
Cowork scheduled task) to run `scripts/run_goal_step.py` every 15 minutes. It
no-ops when the goal is missing or not `active`. Example crontab:

```cron
*/15 * * * * cd /path/to/your/project && python /path/to/goal-kit/scripts/run_goal_step.py
```

For Cowork, ask me: "set up a scheduled task to run goal-step every 15 min in
<project>" and I'll create one with the `mcp__scheduled-tasks__create_scheduled_task`
tool.

**Option B — Agent SDK harness (graduate when needed).** See `sdk-harness/`.
Use this when you want sub-15-minute iteration cadence, hard token budgets,
or programmatic stop detection.

## Why this works

`GOAL.md` is the persistent state. The SessionStart hook makes it impossible
to forget the goal. The slash commands are tiny prompt files that read/write
`GOAL.md`. The loop runner is just `claude -p "do one step"` on a schedule.
Everything's in version control, easy to audit, easy to disable (delete
`GOAL.md` or flip the status to `paused`).

## Design notes

**Per-run JSON archive.** Every iteration's JSON is written to
`.goal-runs/<ISO timestamp>.json` (timestamped, never overwritten) AND to
`.goal-last-run.json` (latest pointer, overwritten each run). The archive
gives you post-hoc visibility — cost-per-iteration, tool-call traces,
permission denials — that's lost if you only have the latest. The latest
pointer keeps the original API working for anything that already reads
`.goal-last-run.json`.

**Sourcing discipline.** The loop runner's prompt and the `/goal` slash
command both enforce a rule: when an iteration cites a source for a factual
claim, the cited source must directly support THAT specific claim. No
adjacent details imported from training that aren't actually in the source.
This catches the failure mode where the agent attaches a real citation to a
plausible-but-unsourced detail (e.g. citing a real product page but
inventing material composition that isn't on it). The rule is enforced at
two layers: every iteration sees it via the script's STEP_PROMPT, and
every new goal generated by `/goal` bakes it into its own Validation
section as a default check.

**Budget enforcement.** GOAL.md can include a `## Budget` section with any
of `max_usd`, `max_iterations`, `max_output_tokens`, `max_input_tokens`.
The Python runner reads it, sums cumulative usage from `.goal-runs/*.json`
before each invocation, and hard-stops when any cap is reached. It also
injects a "Budget status" block into the iteration prompt so the agent can
self-flip Status to `done` when approaching a cap. No separate state file
— the archive is the source of truth. The bash runner enforces only
`max_iterations` (or the `GOAL_MAX_ITERATIONS` env var as a fallback) to
avoid taking on a `jq`-or-Python dependency for budget math; for full
budget control use `run_goal_step.py`.

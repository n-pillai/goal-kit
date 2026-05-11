---
description: Show the current goal, recent progress, and the proposed next step
---

Read `GOAL.md` and produce a concise status report:

1. **Status** (active / paused / inactive / done) and **Objective** (one line).
2. **Last 3 progress log entries**, newest first, verbatim.
3. **Validation snapshot** — for each Validation item, your best guess at its
   current state based on the latest log entries (don't run anything; just
   read).
4. **Proposed next step** — what should the next iteration do? Make this
   concrete and small (one logical change).
5. **Watch-outs** — any Non-goals that the next step risks tripping?
6. **Iteration history** — count files in `.goal-runs/` if it exists, and
   show the timestamps of the most recent 3 runs. (One-line summary, not a
   full file listing.) This gives the user quick visibility into how many
   iterations the loop has spent and when it last ran. If `.goal-runs/`
   doesn't exist, just say "no archived runs yet."
7. **Budget usage** — if GOAL.md has a `## Budget` section, sum the
   `total_cost_usd` and `usage.{input,output}_tokens` from every JSON in
   `.goal-runs/` and report each dimension as "$X.XX of $Y.YY (Z%)". If no
   Budget section, say "no budget set." Flag any dimension above 80% so the
   user can decide to pause early.

Keep it tight: under ~30 lines total. Use a short markdown structure, not
prose paragraphs.

If `GOAL.md` doesn't exist or status is `inactive`, say so and suggest
`/goal <objective>`.

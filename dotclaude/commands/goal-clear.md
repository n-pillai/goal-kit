---
description: Archive the current goal and reset GOAL.md to the template
---

Clearing is destructive — confirm with the user before doing it.

1. Read `GOAL.md`. Show its Objective and Status to the user, then ask:
   "Archive and clear this goal? (yes/no)"

2. If they confirm:
   a. Create `goal-archive/` if it doesn't exist.
   b. Move the current `GOAL.md` to `goal-archive/GOAL-<ISO timestamp>.md`
      (e.g. `GOAL-2026-05-08T14-22-03Z.md` — colons replaced with dashes for
      filesystem safety).
   c. Reset `GOAL.md` to the empty template (Status: inactive, all sections
      back to `_(unset)_` / `_(empty)_`).
   d. Tell the user the archive path and that GOAL.md is reset.

3. If they decline, do nothing.

Use a real timestamp from `date -u` or Python. Do not delete the archive;
old goals are useful audit trail.

**Do NOT delete `.goal-runs/`.** That directory is the per-iteration JSON
archive (separate from the GOAL.md archive in `goal-archive/`) and contains
historical run data — costs, tool calls, permission denials — that may be
useful for analyzing past loops. If the user wants a clean slate, they can
delete it themselves; this command should leave it alone.

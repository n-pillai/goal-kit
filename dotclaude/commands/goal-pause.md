---
description: Pause the active goal (loop runner will skip; hook stops injecting)
argument-hint: [optional reason]
---

Read `GOAL.md`.

- If status is `active`: change `**Status:** active` to `**Status:** paused`,
  then append a single progress log entry at the TOP of the Progress log
  section in this format:
  `<ISO 8601 UTC timestamp> | paused | n/a | reason: $ARGUMENTS (or "no reason given")`
  Save the file. Confirm to the user: "Goal paused. Loop runner will skip
  until you `/goal-resume`."

- If status is anything else (`paused`, `inactive`, `done`): tell the user
  the current status and do nothing.

Use Python (or `date -u +%Y-%m-%dT%H:%M:%SZ`) to get the timestamp; do not
fabricate one.

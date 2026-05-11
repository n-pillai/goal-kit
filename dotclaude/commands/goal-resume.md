---
description: Resume a paused goal and propose the next step
---

Read `GOAL.md`.

- If status is `paused`: change to `active`, append a single progress log
  entry at the TOP:
  `<ISO 8601 UTC timestamp> | resumed | n/a | next: <your proposed next step>`
  Save the file. Then show the user: the Objective (one line), the most
  recent prior progress entry (the one just before "paused"), and your
  proposed next step. Ask if they want to run that next step now or let the
  scheduled loop pick it up.

- If status is `active`: tell the user it's already active; show
  `/goal-status` style summary.

- Any other status: tell the user the current status and stop.

Use a real timestamp (`date -u` or Python), not a placeholder.

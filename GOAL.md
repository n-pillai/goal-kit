# Goal

**Status:** inactive

<!--
Status values:
  inactive  - no goal set; SessionStart hook does not inject this file
  active    - goal is being pursued; loop runner will execute steps; hook injects context
  paused    - goal is preserved but loop runner skips; hook does not inject
  done      - terminal state; goal completed (one of the Stop conditions fired)
-->

## Objective

<!-- What durable outcome are you pursuing? Bigger than one prompt, smaller than an open-ended backlog. -->

_(unset)_

## Non-goals

<!-- Boundaries: files, behaviors, or scope that must NOT change. The agent reads this every iteration. -->

- _(unset)_

## Validation

<!-- How does the agent know it's making real progress? Concrete commands or signals. -->

<!--
If this goal involves factual claims, research, or any sourced output,
ALWAYS include this rule (the /goal slash command does this automatically;
this comment is the fallback for hand-authored goals):

"Every cited source must directly support the specific claim it's attached
to. No adjacent details from training that aren't in the source — drop
them, or label as opinion."
-->

- _(unset)_

## Budget

<!-- Optional. If set, the runner enforces these as HARD caps before
     invoking claude (skips the run when reached) AND injects a "Budget
     status" block into every iteration's prompt so the agent can self-stop
     early. Omit any field to leave that dimension uncapped.

     Fields the runner understands:
       - max_usd: <dollars>         e.g. 20.00
       - max_iterations: <int>      e.g. 12
       - max_output_tokens: <int>   e.g. 500000
       - max_input_tokens: <int>    e.g. 5000000

     The .py runner enforces all four. The .sh runner enforces only
     max_iterations (or the GOAL_MAX_ITERATIONS env var if unset).
-->

- max_usd: 20.00
- max_iterations: 12

## Stop conditions

<!-- When should the loop halt? Examples: "all tests in tests/ pass", "PR opened",
     "5 consecutive iterations without a green validation", "approaching any Budget cap". -->

- _(unset)_

## Progress log

<!-- Newest entries on top. Each entry, on a single line:
     - <ISO timestamp> | <action taken> | <validation outcome> | <planned next step>
-->

_(empty)_

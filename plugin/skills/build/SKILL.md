---
name: build
description: Build every reviewed plan end to end without stopping - run the experiment, execute phase by phase in build order, decide and record instead of asking, commit at every gate, and stop only for the hard stops in caddis.md.
---

Build the reviewed plans in `.caddis/projects/active/`, in build order, or the ones named in my
message. **Do not stop to ask for permission or confirmation.** The plans were reviewed so
this can run unattended.

## Before starting

- Read `.caddis/caddis.md`, in particular Hard stops and Machine limits.
- Every plan in scope has a `**Reviewed:**` line. If one doesn't, review it as the `review`
  skill does, but take each open question's default instead of asking. Record each as
  `(default, YYYY-MM-DD)` and mark it `**Reviewed:** YYYY-MM-DD (defaults, no owner input)`.
- Run the `learn` skill if it hasn't run this session.

## The loop

For each plan, in order:

1. **Experiment first**, if the plan has one: run every variant through the real code path
   with the benchmark command, one heavy job at a time, and write the results table into the
   plan. Implement only the winner. If nothing beats the baseline, record that and complete
   the plan as not adopted.
2. For each phase: run the `execute` skill on it, pass the gate (lint, typecheck, tests, the
   phase's own checks), then `commit`.
3. When the plan is done: `complete`, `commit`, next plan.

Keep going until every plan in scope is complete. `/caddis:build` never writes a new plan:
when the reviewed plans are done, name the next one worth writing and stop.

## When something comes up

- **A decision the plan didn't make:** pick the option that best fits caddis.md, the
  docs it lists (the Architecture doc and any doc on how the project works or what it
  values) and the plan. Record it under `## Decisions During Build` with a one-line
  reason. Continue.
- **The plan is wrong:** fix the plan, record what changed and why, continue.
- **A failing gate:** fix the root cause. Try at least three different approaches before
  calling it blocked. Never weaken a test or silence a check to pass.
- **Blocked for real** (a missing account, key or hardware the build can't create): record
  it in the plan, skip only what depends on it, carry on with the rest.
- **The work grew past the plan:** finish what the plan covers, note the rest as a follow-up.

## The only reasons to stop and wait

The Hard stops in `.caddis/caddis.md`. Everything else is decided and recorded.

## Output

When done, or when only hard stops remain: plans completed, commits made, decisions taken,
anything blocked and what would unblock it. Short.

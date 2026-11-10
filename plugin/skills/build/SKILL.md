---
name: build
description: Build every reviewed project end to end without stopping - run the experiment, execute phase by phase in build order, decide and record instead of asking, commit at every gate, and stop only for the hard stops in caddis.md.
---

Build the reviewed projects in `.caddis/projects/active/`, in build order, or the ones named in my
message. **Do not stop to ask for permission or confirmation.** The projects were reviewed so
this can run unattended.

## Run it in the background

If you are the background builder, skip this section. Otherwise, in the main session:

1. List the projects in scope and estimate the build in minutes from their phases and Changes.
   Tell me the estimate in one line.
2. Note the start time with `date +%s`. Start one background `general-purpose` agent: "You
   are the background builder. Run the `caddis:build` skill on these projects: <paths>."
   Include anything else from my message.
3. Start the Monitor tool with `bash <this skill's scripts folder>/progress.sh <start>
   <estimate> <project paths>` and a `timeout_ms` of 1800000. The script stays silent on short
   builds and sets its own report interval as the estimate changes.
4. Pass each status line to me as it arrives, in one line. On `Possibly stuck`, say so and
   leave the agent running: a long check can look the same. If the monitor expires while the
   agent is running, start it again with the same arguments.
5. When the agent finishes, stop the monitor with TaskStop and give me its report. If it is
   waiting on a hard stop, ask me, then pass my answer on with SendMessage.

If the Agent or Monitor tool isn't available, build in this session instead.

The builder can't ask me anything. It sends blockers and hard stops to `main` with
SendMessage, along with any decision I'd want to hear about before the end.

## Before starting

- Read `.caddis/caddis.md`, in particular Hard stops and Machine limits.
- Every project in scope has a `**Reviewed:**` line. If one doesn't, review it as the `review`
  skill does, but take each open question's default instead of asking. Record each as
  `(default, YYYY-MM-DD)` and mark it `**Reviewed:** YYYY-MM-DD (defaults, no owner input)`.
- A project marked `**Signed off:** pending` still builds, unless caddis.md's Wait for
  sign-off is yes: then skip it and any project that depends on it. Either way, list it as
  waiting for product sign-off. Never sign off for the product owner.
- Run the `learn` skill if it hasn't run this session.

## The loop

For each project, in order:

1. **Experiment first**, if the project has one: run every variant through the real code path
   with the benchmark command, one heavy job at a time, and write the results table into the
   project. Implement only the winner. If nothing beats the baseline, record that and complete
   the project as not adopted.
2. For each phase: run the `execute` skill on it, pass the gate (lint, typecheck, tests, the
   phase's own checks), then `commit`.
3. When the project is done: `complete`, `commit`, next project.

Keep going until every project in scope is complete. `/caddis:build` never writes a new project:
when the reviewed projects are done, name the next one worth writing and stop.

## When something comes up

- **A decision the project didn't make:** pick the option that best fits caddis.md, the
  docs it lists (the Architecture doc and any doc on how the project works or what it
  values) and the project. Record it under `## Decisions During Build` with a one-line
  reason. Continue. If every option breaks something the Summary promises users, take the
  closest, record it, and list it in the output for the product owner.
- **The project is wrong:** fix the project, record what changed and why, continue.
- **A failing gate:** fix the root cause. Try at least three different approaches before
  calling it blocked. Never weaken a test or silence a check to pass.
- **Blocked for real** (a missing account, key or hardware the build can't create): record
  it in the project, skip only what depends on it, carry on with the rest.
- **The work grew past the project:** finish what the project covers, note the rest as a follow-up.

## The only reasons to stop and wait

The Hard stops in `.caddis/caddis.md`. Everything else is decided and recorded.

## Output

When done, or when only hard stops remain: projects completed, commits made, decisions taken,
anything blocked and what would unblock it. Short.

---
name: build
description: Build every reviewed project end to end without stopping - run the experiment, execute phase by phase in build order, decide and record instead of asking, commit at every gate, and stop only for the hard stops in caddis.md.
---

Build the projects named in my message, in build order. With none named, take the reviewed
projects in `.caddis/projects/active/` that this branch added or changed since it left the
default branch; on the default branch, or if there are none, all reviewed ones. **Do not stop to ask for permission or confirmation.** The projects were reviewed so
this can run unattended.

**Team rules.** If `.caddis/extend/build.md` exists, read it before anything else and
follow it. It adds to or overrides this skill, but it never removes a hard stop, weakens a
gate, silences a check or skips the gate-verifier.

## Run it in the background

If you are the background builder, skip this section. Otherwise, in the main session:

1. Run Before starting below once, here, for every project in scope. Builders skip it.
2. **Plan the waves.** Run `python3 <this skill's scripts folder>/waves.py --ignore <files>
   <project paths>`, with the files on Workflow's Merge by rule line. Leave `--ignore` out
   when the line is missing or says none. It prints JSON: `waves`, each a list of projects that share no file and
   depend only on earlier waves, and `sequenced`, the projects waiting on another because
   they share files.
3. List the projects in scope, the waves, and an estimate in minutes from their phases and
   Changes (the longest project per wave, summed). Tell me the estimate in one line.
4. Note the start time with `date +%s`. Start the Monitor tool with `bash <this skill's
   scripts folder>/progress.sh <start> <estimate> <every project path>` and a `timeout_ms`
   of 1800000. One reporter covers every wave and builder. It stays silent on short builds
   and sets its own report interval as the estimate changes. The build panel and its status
   line follow the file it writes; nothing for the builders to do.
5. **Each wave in turn:**
   - A wave of one project: one background `caddis:builder` agent, in this checkout.
   - A wave of several: one background `caddis:builder` agent per project with
     `isolation: "worktree"`, up to Parallel agents at once (start the rest as others
     finish). The build branch must be checked out at its tip, so every worktree branches
     from it. Each builder makes its own `caddis/<project>` branch there.
   - Give each builder its project path (absolute, in this checkout), this checkout's
     absolute path and anything else from my message. Its standing brief holds the rules.
   - When every builder in a parallel wave is done, start the `caddis:integrator` agent
     with the build branch, this checkout's path and the wave's projects in build order,
     each with its branch and worktree. Wait for it before the next wave. A project it
     couldn't merge stays on its branch: skip any later project that depends on it, and
     tell me which ones are marked complete but not merged.
6. Pass each status line to me as it arrives, in one line. On `Possibly stuck`, say so and
   leave the agents running: a long check can look the same. If the monitor expires while
   an agent is running, start it again with the same arguments.
7. When the last wave is done, stop the monitor with TaskStop and give me the builders' and
   integrator's reports as one. If a builder is waiting on a hard stop, ask me, then pass
   my answer on with SendMessage.

Fall back to one `caddis:builder` for every project in build order, as before waves, when
there is only one project, `waves.py` fails, or a worktree can't be made. If the Agent or
Monitor tool isn't available, or the `caddis:builder` agent isn't, build in this session.

Builders can't ask me anything. They send blockers and hard stops to `main` with
SendMessage, along with any decision I'd want to hear about before the end.

## Before starting

- Read `.caddis/caddis.md`, in particular Workflow, Hard stops and Machine limits: one of
  its Heavy jobs at a time (default: a full build, a benchmark, a model load), and no more
  background agents at once than Parallel agents (default: no cap).
- Every project in scope has a `**Reviewed:**` line. If one doesn't and Workflow's
  Unreviewed projects is `skip`, leave it out and say so. Otherwise review it as the
  `review` skill does, but take each open question's default instead of asking. Record each
  as `(default, YYYY-MM-DD)` and mark it `**Reviewed:** YYYY-MM-DD (defaults, no owner input)`.
- A project marked `**Signed off:** pending` waits, unless Workflow's Wait for sign-off is
  no. First check the ticket or PR for an approval and record it as the `review` skill
  does. Skip a project still waiting and any project that depends on it, and list them as
  waiting for product sign-off. Never sign off for the product owner.
- Run the `learn` skill if it hasn't run this session.

## The loop

For each project, in order:

1. **Experiment first**, if the project has one: run every variant through the real code path
   with the benchmark command, one heavy job at a time, and write the results table into the
   project. Implement only the winner. If nothing beats the baseline, record that and complete
   the project as not adopted.
2. Run the `execute` skill on the project. It gates and commits each phase and completes
   the project. If it pauses (Workflow's Pause after each phase), stop and report: the
   phase done, what's next. Running `/caddis:build` again carries on.
3. Next project.

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

The Hard stops in `.caddis/caddis.md`, and any pause the Workflow section or
`.caddis/extend/build.md` asks for. Everything else is decided and recorded.

## Output

When done, or when only hard stops remain: projects completed, commits made, decisions taken,
anything blocked and what would unblock it. Short.

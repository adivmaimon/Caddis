---
name: project
description: Write a project file for a piece of work into .caddis/projects/active/ as project-<name>.md, without implementing it. Use when the user asks to create a project, write a plan or plan out a feature, including from an intent file or a ticket key. Triages small low-risk work to /caddis:task instead.
---

Write a project file for the work described in my message. Do not implement it.

**Team rules.** If `.caddis/extend/project.md` exists, read it before anything else and
follow it. It adds to or overrides this skill, but it never removes a hard stop, weakens a
gate, silences a check or skips the gate-verifier.

## 0. Triage first

Read `.caddis/caddis.md`. If the work meets every condition for a task (see the
`task` skill: small, one layer, nothing on the Risk list, no Invariant touched, no
experiment needed), say so in one line and follow the `task` skill instead. If unsure,
it is a project.

## 1. Gather

- **The intent.** If my message names an intent file or a ticket key, read it (a ticket
  with the tracker tool in caddis.md's Product section). It is the brief: the project delivers
  its Outcome and Done when, and stays inside Out of scope. Link it; don't copy it. If the
  work changes what users see and caddis.md lists Product owners but there is no intent,
  say so in one line and carry on.
- Read `.caddis/caddis.md` and `.caddis/map/STRUCTURE.md`. If the map is missing or
  `python3 .caddis/bin/map.py status` says it is stale for the areas involved,
  refresh it first with the `map` skill.
- Read the docs listed under Docs in `caddis.md`, and at least one existing project in
  `.caddis/projects/active/` or `.caddis/projects/completed/` to match tone and shape.
- Read the code the project will touch. Use `python3 .caddis/bin/map.py uses <file>` to find
  what depends on it. Name nothing the code has not confirmed.
- If a Reference repo already solved this, read how.

## 2. Write

File: `.caddis/projects/active/project-<kebab-name>.md`. Concrete and technical, not
corporate. Short: about 60 lines for one phase, and each phase of a longer project fits on one
screen. **Leave out any section with nothing to say.** No "None" or "Skipped" lines; a
missing section means none. Goal, Summary, Context, Changes and Verification are always
there.

If the project changes a decision recorded in the Architecture doc or `caddis.md`, say so
plainly and argue for it. Never diverge quietly.

### Template

```markdown
# <Title>

**Status:** Pending
**Type:** Project | Master plan
**Phases:** <n>
**Depends on:** <project files, or None>
**Intent:** <intent file name or ticket key, or None>

## Goal
One sentence: what this achieves and why it matters to the user.

## Summary
For the product owner and anyone non-technical. Plain-language bullets: what changes for
users and why. Then:
**Done when:** the intent's checks, in its words (or your own, in product terms).
**Questions for product:** only scope or behaviour questions, each with a suggested answer.

## Context
What exists now, what is missing or broken. File paths and line numbers.

## Risk
Low / Medium / High and why, using caddis.md's Risk list. Mitigation: phasing, reduced
scope, flag, rollback. The metric or test that would catch a regression.

## Experiment
Only when caddis.md has Experiments set and this changes behaviour: variants (the approach,
real alternatives, current behaviour as baseline), how each runs (the real code path, the
benchmark command, nothing mocked), the Metrics that matter, the Threshold to adopt, and a results table
filled in before implementation starts.

## Key Reference Files
Files to read but not edit: the Architecture doc section, reference repo files.

## Changes
Every file that changes and how: functions, types, constants, new and deleted files. A
table if long. Name what is **reused**. Before proposing a new module, say what was
searched and why nothing existing fits.

## Invariants
Which numbered Invariants this touches and how each holds.

## Storage & State
Migrations, new files, settings keys, upgrade path for existing data.

## Phases
For large, risky or multi-layer work. Each phase: what it delivers and a gate a machine can
check (a test, a measurement, a file that exists). Each phase ends in its own commit. Lint,
typecheck and tests green are implied for every gate.

### Phase 1 - <name>
...

## Tests
New and changed logic to test, highest value first, per caddis.md's Tests priorities.

## Verification
Numbered end-to-end steps. Name the automated checks.

## Open Questions
Technical questions, each with a recommended default. /caddis:review asks the owner once;
the build never stops to ask.
```

The Summary follows the Writing rules in caddis.md's Product section. It is the only part
a product owner needs to read, and the part they sign off.

If caddis.md's Plans section lists Required sections, write those in their stated format at
the end. They replace `## Summary` unless Keep Summary is yes or
Product is on (caddis.md's Product owners line names someone). Follow its Other rules. A project with nothing for those readers gets the
Silent marker instead, if one is defined.

### Charts and flows

Optional; prose and tables are always fine. Each is YAML in a fenced block. Use Mermaid for
any other diagram.
- ` ```chart `: `title`, `better` (`lower` or `higher`), `rows` of `[label, number]` with an
  optional third item `winner` or `rejected`; optional `threshold` and `note`. For
  Experiment results.
- ` ```flow `: `title`, `steps` (name: detail, in order), optional `branch` list of
  `{from, if, to, tone}` where `from` and `to` name steps and `tone` is `good`, `bad` or
  `neutral`. For a lifecycle or state change the project introduces.

## 3. Check

Re-read the project against the code and the intent: every file named exists or is created by
the project, every Done when check is covered by Verification, nothing outside Out of scope is
built, every risk and side effect is covered, nothing is assumed. Fix it, then confirm the
filename and scope in two lines.

## Rules

- Master plans (`Type: Master plan`) list phases that each become their own project later.
- The project lands as its own `docs:` commit via the `commit` skill, unless `.caddis/` is
  gitignored (then there is nothing to commit).
- Phase headings must be `### Phase N - <name>` so progress tools can read them.
- An intent file that this project delivers gets `**Status:** Planned (project-<name>)`.

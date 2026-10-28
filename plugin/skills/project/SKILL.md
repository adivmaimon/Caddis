---
name: project
description: Write a plan for a piece of work into .caddis/projects/active/ as project-<name>.md, without implementing it. Use when the user asks to create a project, write a plan or plan out a feature. Triages small low-risk work to /caddis:task instead.
---

Write a plan for the work described in my message. Do not implement it.

## 0. Triage first

Read `.caddis/caddis.md`. If the work meets every condition for a task (see the
`task` skill: small, one layer, nothing on the Risk list, no Invariant touched, no
experiment needed), say so in one line and follow the `task` skill instead. If unsure,
it is a project.

## 1. Gather

- Read `.caddis/caddis.md` and `.caddis/map/STRUCTURE.md`. If the map is missing or
  `python3 .caddis/bin/map.py status` says it is stale for the areas involved,
  refresh it first with the `map` skill.
- Read the docs listed under Docs in `caddis.md`, and at least one existing plan in
  `.caddis/projects/active/` or `.caddis/projects/completed/` to match tone and shape.
- Read the code the plan will touch. Use `python3 .caddis/bin/map.py uses <file>` to find
  what depends on it.
  Name nothing the code has not confirmed.
- If a Reference repo already solved this, read how.

## 2. Write

File: `.caddis/projects/active/project-<kebab-name>.md`. About 100 lines for one phase; each phase
of a longer plan fits on one screen. Concrete and technical, not corporate.

If the plan changes a decision recorded in the Architecture doc or `caddis.md`, say so
plainly and argue for it. Never diverge quietly.

### Template

```markdown
# <Title>

**Status:** Pending
**Type:** Project | Master plan
**Phases:** <n>
**Depends on:** <plan files, or None>

## Goal
One sentence: what this achieves and why it matters to the user.

## Context
What exists now, what is missing or broken, what the user would notice. File paths and
line numbers.

## Risk
Low / Medium / High and why, using caddis.md's Risk list. Mitigation: phasing, reduced
scope, flag, rollback. Name the metric or test that would catch a regression.

## Experiment
Only when caddis.md has Experiments set and this changes behaviour. Otherwise one line:
"Skipped: <reason>".
- Variants: the approach, real alternatives, and current behaviour as the baseline
- How each runs: the real code path, the benchmark command, nothing mocked
- Measures: the metrics from caddis.md that can move
- Winner: the threshold, and what happens if nothing beats the baseline
- Results: a table filled in before implementation starts

## Key Reference Files
Paths: files being edited, the Architecture doc section, reference repo files.

## Changes
Every file that changes and how: functions, types, constants, new and deleted files. A
table if long. Name what is **reused**. Before proposing a new module, say what was
searched and why nothing existing fits.

## Invariants
Which numbered Invariants this touches and how each holds. "None touched" if so.

## Storage & State
Migrations, new files, settings keys, upgrade path for existing data. "None" if so.

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
Each with a recommended default. /caddis:review asks the owner once; the build never stops
to ask.

## Summary
Plain-language bullets for a non-developer: what changes and why it matters.
```

If caddis.md's Plans section lists Required sections, write those in their stated format in
place of `## Summary` (or as well, if it says Keep Summary), and follow its Other rules. A
plan with nothing for those readers gets the Silent marker instead, if one is defined.

## 3. Check

Re-read the plan against the code: every file named exists or is created by the plan,
every risk and side effect is covered, nothing is assumed, the Plans sections are present and
well formed. Fix it, then confirm the filename
and scope in two lines.

## Rules

- Master plans (`Type: Master plan`) list phases that each become their own plan later.
- The plan lands as its own `docs:` commit via the `commit` skill, unless `.caddis/` is
  gitignored (then there is nothing to commit).
- Phase headings must be `### Phase N - <name>` so progress tools can read them.

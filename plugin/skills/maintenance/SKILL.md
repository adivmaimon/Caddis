---
name: maintenance
description: Run the periodic (monthly) maintenance pass over the whole codebase - the repo's own maintenance skills, benchmark health, invariant audit, reuse sweep, comments, performance, AI cost, tests, lint and build, dependencies, security, docs and map accuracy - with read-only sweeps handed to the auditor agent, logging results and carry-over in .caddis/maintenance-log.md.
---

Run across the whole codebase, not just recent changes. Report and fix small things in
the pass; anything bigger becomes a plan via the `project` skill.

**Before starting:** read `.caddis/maintenance-log.md` (create it from the template below if
missing). It holds carry-over from the last pass. Don't re-report what it has settled.
Skip any step whose subject doesn't exist yet and say so.

**Sweeps go to the `auditor` agent.** Steps marked *(auditor)* below are read-only sweeps:
hand each to the auditor with its focus, any scope, and the log's settled items for that
focus. Keep its findings, not the files. Fix `in-pass` findings yourself, then rerun the
checks; group `plan` findings into plans with the `project` skill. Run auditors in parallel
only when caddis.md's Machine limits allow it, otherwise one at a time. On a large repo,
give each auditor one area of the map at a time. Steps that run commands (benchmark, lint
and build, dependencies) stay with you.

## 0. Local skills
Run every skill marked `Maintenance:` under Local skills in caddis.md, honouring its ordering
note: start long-running or background ones first and carry on with the steps below while
they run, respecting Machine limits. Where a local skill covers a step (performance, UI,
docs), take its findings for that step instead of repeating the work. Wait for every one to
finish before the log, and record each one's result, or why it didn't run.

## 1. Benchmark
If caddis.md has Experiments: run the benchmark (report only), compare to the last
baseline. Any regression becomes a plan.

## 2. Invariant audit *(auditor: invariants)*
Every path that matters for each numbered Invariant in caddis.md is enforced and labelled.

## 3. Reuse *(auditor: reuse)*
Repeated logic, near-duplicates, raw values that should be tokens, dead files.

## 4. Comments *(auditor: comments)*
Missing headers and provenance, stale or narrating comments, commented-out code.

## 5. Performance *(auditor: performance, then you)*
The auditor finds likely hot spots from the code. You measure the numbers that matter for
this project (load time, response time, memory, bundle size), one heavy job at a time, and
compare to the last pass.

## 5b. AI cost *(auditor: ai-cost)*
Only when caddis.md's Stack includes a model. Anything that needs measuring goes through
the repo's benchmark, not the auditor.

## 6. Tests *(auditor: tests, then you)*
The auditor finds untested priorities and hollow tests. You run the suite: it is green at
baseline, and any failure is a regression, never "pre-existing".

## 7. Lint, types, build
Every command in caddis.md's Commands, one heavy job at a time. Zero warnings.

## 8. Dependencies
Outdated or vulnerable packages in every manifest (`npm audit`, `pip-audit`,
`cargo audit` or the equivalent). Log upgrades for a scoped plan; don't upgrade mid-pass.

## 9. Security and privacy *(auditor: security)*
Secrets, user data in logs, unvalidated input, data leaving where it shouldn't.

## 10. Docs and map *(auditor: docs, then you)*
The auditor checks the docs and skills against the tree. You run the `map` skill in full
mode and compare.

## After all steps

Add a row to the table in the log, rewrite its **Last Run** section with carry-over, and
add a `### Notes - YYYY-MM-DD` block with detail, including a line per local skill run.

### Log template

```markdown
# Maintenance log

| Date | Steps | Summary |
| --- | --- | --- |

## Last Run
Carry-over: open items, things investigated and rejected.
```

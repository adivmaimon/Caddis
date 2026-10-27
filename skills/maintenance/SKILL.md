---
name: maintenance
description: Run the periodic (monthly) maintenance pass over the whole codebase - benchmark health, invariant audit, reuse sweep, comments, performance, tests, lint and build, dependencies, security, docs and map accuracy - logging results and carry-over in .caddis/maintenance-log.md.
---

Run across the whole codebase, not just recent changes. Report and fix small things in
the pass; anything bigger becomes a plan via the `project` skill.

**Before starting:** read `.caddis/maintenance-log.md` (create it from the template below if
missing). It holds carry-over from the last pass. Don't re-report what it has settled.
Skip any step whose subject doesn't exist yet and say so.

## 1. Benchmark
If caddis.md has Experiments: run the benchmark (report only), compare to the last
baseline. Any regression becomes a plan.

## 2. Invariant audit
Walk every path that matters for each numbered Invariant in caddis.md and confirm it is
enforced and labelled. Look for new code that bypasses one.

## 3. Reuse
Logic, markup or styles repeated three or more times that can be safely extracted.
Near-duplicate components or helpers. Raw values that should be tokens or constants. Run
`python3 .caddis/bin/map.py orphans` for files nothing imports and confirm each is an entry
point or dead.

## 4. Comments
Missing file headers, constants without provenance, unlabelled invariant enforcement,
comments that narrate the obvious, commented-out code.

## 5. Performance
The numbers that matter for this project (load time, response time, memory, bundle size).
Compare to the last pass.

## 6. Tests
Important logic without tests, especially caddis.md's test priorities. The suite is green
at baseline; any failure is a regression, never "pre-existing".

## 7. Lint, types, build
Every command in caddis.md's Commands, one heavy job at a time. Zero warnings.

## 8. Dependencies
Outdated or vulnerable packages in every manifest (`npm audit`, `pip-audit`,
`cargo audit` or the equivalent). Log upgrades for a scoped plan; don't upgrade mid-pass.

## 9. Security and privacy
Secrets in the repo or history, user data in logs, unvalidated input at boundaries, network
calls carrying data they shouldn't.

## 10. Docs and map
`CLAUDE.md`, caddis.md, the Architecture doc, the README and the skills match the tree:
paths, commands, names, decisions. Run the `map` skill in full mode and compare.

## After all steps

Add a row to the table in the log, rewrite its **Last Run** section with carry-over, and
add a `### Notes - YYYY-MM-DD` block with detail.

### Log template

```markdown
# Maintenance log

| Date | Steps | Summary |
| --- | --- | --- |

## Last Run
Carry-over: open items, things investigated and rejected.
```

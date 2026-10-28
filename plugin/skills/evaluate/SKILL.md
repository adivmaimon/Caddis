---
name: evaluate
description: Investigate whether a proposed change, feature, refactor, library or model choice is a good idea - report verdict, impact per layer, effort, risk and alternatives. Research only, no implementation. Feeds /caddis:project.
---

Investigate what my message describes and write a structured evaluation. Do not implement.

## Rules

- Lead with the verdict. If it is not a good idea, say so plainly and why.
- Read, don't guess. Every claim about the code cites a file.
- Measure when measuring is cheap. A short spike (speed, memory, bundle size, start time)
  beats an argument. Spikes live in a scratch directory outside the repo and are deleted.
  Respect caddis.md's Machine limits.
- Every section filled, briefly.

## Explore

1. Read `.caddis/caddis.md` and `.caddis/map/STRUCTURE.md`. Find the areas involved.
2. Grep for existing usages of whatever is replaced or extended. For key files, run
   `python3 .caddis/bin/map.py uses <file>` to see the blast radius.
3. Read the Architecture doc. A proposal that contradicts it must say so and argue for the
   change.
4. Check dependency manifests for what already exists.
5. Find tests and benchmark cases that would need to change.
6. If a Reference repo already solved this, read how and say whether it fits.
7. For a library or service choice, check it is maintained and what it costs.

When the idea touches a wide area (several map areas, or a cross-cutting concern such as
performance or security), hand the sweep to the `auditor` agent with that focus and scope
instead of reading it all yourself, and build the report on its findings.

## Report

### Verdict
**Feasible**, **Feasible with caveats**, or **Not recommended**, and the main reason.

### What's Being Evaluated
One paragraph: exactly what, and which user outcome it serves.

### Impact by Layer
One short subsection per layer in caddis.md's Layers that this touches: files, modules,
new dependencies, data. "None" for untouched layers, in one line.

### Invariants
Which numbered Invariants are at stake and whether they can hold.

### Effort
Files affected, rough complexity, unknowns. What can be reused or ported.

### Risk
Low / Medium / High per caddis.md's Risk list. What could regress, whether it is
reversible.

### Alternatives Considered
At least one, and why it loses or might win.

### Recommended Next Step
"Write a project with /caddis:project", "Small enough for /caddis:task", or what would have
to change to make it feasible.

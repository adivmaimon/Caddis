---
name: review
description: Review the active plans before a build - check them against caddis.md, the architecture doc, the code and each other, fix what can be fixed, ask the owner every open question in one batch, and mark each plan Reviewed so /caddis:build can run without stopping.
---

Review every plan in `.caddis/projects/active/`, or the ones named in my message. The goal is a set
of plans `/caddis:build` can run start to finish without asking anything.

## Steps

1. **Read** `.caddis/caddis.md`, `.caddis/map/STRUCTURE.md`, the Architecture doc and every
   plan in scope. Work out the build order from each plan's `Depends on` line.
2. **Check each plan:**
   - It agrees with caddis.md, the Architecture doc and the other plans. Fix contradictions
     in the plan, or in the docs if the plan is right.
   - Every file, command and path it names exists, or an earlier plan creates it. Verify
     against the tree, not memory.
   - Every phase has a gate a machine can check: a test, a measurement, a file that exists.
   - It names the Invariants it touches and how each holds.
   - Its Risk level matches caddis.md's Risk list.
   - If caddis.md has Experiments set and the plan changes behaviour, it has an Experiment
     phase first with variants, a baseline, real measures and a rule for the winner.
   - Dependencies between plans are explicit and the order respects them.
   - Any user-facing copy follows the Brand doc, if there is one.
   - It carries the sections caddis.md's Plans section requires, in the stated format, or
     the Silent marker. With no Plans config, a plain-language `## Summary`.
   Then hand each plan to the `plan-reviewer` agent (just the plan's path) for a fresh read
   without your context. Run them one at a time if caddis.md's Machine limits rule out
   parallel agents. Treat its blocking findings as yours to fix; judge its minor ones.
3. **Fix what you can** directly: stale paths, missing gates, wrong order, vague steps.
4. **Collect every question that needs the owner** across all plans, including each plan's
   Open Questions. Ask them **once, together**, each with a recommended answer. Ask only
   what changes what gets built; decide the rest and record it.
5. **Write the answers in** as decisions `(owner, YYYY-MM-DD)`. Give every remaining open
   question a default the build will use.
6. **Mark each plan** with `**Reviewed:** YYYY-MM-DD` under its Status line.
7. **Commit** the reviewed plans as one `docs:` commit with the `commit` skill, unless
   `.caddis/` is gitignored.

## Output

- Plans reviewed and what was fixed in each
- Owner decisions and defaults chosen
- The build order
- "Ready for /caddis:build", or the one thing blocking it

## Rules

- No code. This is the last point the owner is asked anything before the build.
- Don't ask what the docs, the code or a sensible default already answers.

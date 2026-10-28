---
name: execute
description: Execute one active plan end to end - read it, confirm the code matches, implement phase by phase, pass each gate, test, commit each chunk and complete it. Use for a single plan; /caddis:build runs this across many.
---

Execute the plan named in my message, or the most recently discussed active plan.

## 1. Load

1. Find the file in `.caddis/projects/active/` and read all of it before writing code.
2. Read `.caddis/caddis.md`. Its Invariants, Commands and Machine limits apply throughout.
3. If it is a master plan (`Type: Master plan`), don't implement it directly: each phase
   becomes its own plan via the `project` skill, unless the phase says it is a spike or a
   decision with no feature code.
4. If the plan is ambiguous or contradicts the code, the code wins. Fix the plan, record it
   under `## Decisions During Build`, and carry on. Never diverge silently.

## 2. Explore

Read every file in Changes and Key Reference Files before writing to it. Plans go stale;
confirm the code still matches. Check `.caddis/map/STRUCTURE.md` for where new things
belong, and `python3 .caddis/bin/map.py uses <file>` before changing anything shared.

## 3. Implement

Work through Changes one file at a time, phase by phase.

- **Invariants hold on every path.** Label the code that enforces one.
- **Reuse.** Grep before writing. Extend an existing module before adding a near
  duplicate. Extract on the second use, not the first. Where a Reference repo has a working
  answer, port what fits and say so in the completion notes.
- **Comments.** A header on every new file. Why, not what. Provenance on every tuning
  constant.
- **Check as you go.** Run lint, typecheck and format from caddis.md after each meaningful
  file. Never silence a rule to get green.
- **No scope creep.** Note unrelated problems for the summary; don't fix them here.

## 4. Gate each phase

1. Walk the phase's gate and the plan's Verification steps that apply. Report each as
   passed, failed or skipped with the reason. Fix root causes.
2. If the plan has Tests, write them with the `tests` skill. Run the full suite. If a
   pre-existing test fails, decide on purpose whether the test or the change is wrong.
3. Hand the phase to the `gate-verifier` agent: the plan path and phase number, nothing
   about what you did. On **FAIL**, fix the root cause and verify again. If it still fails
   after two rounds, record the finding under `## Decisions During Build` and treat the
   gate as failed. On **INCOMPLETE** for a heavy check, run that check yourself. Skip the
   agent for a phase that only changes docs.
4. Mark the phase heading done: `### Phase 2 - <name> - DONE (YYYY-MM-DD)`. Progress tools
   read this marker.
5. Commit the phase with the `commit` skill. Never commit a failing gate. Don't push.

## 5. Complete

Run the `complete` skill, commit that as its own `docs:` commit, and summarise: files
changed, decisions taken, deviations from the plan and why, anything skipped, follow-ups.

## Rules

- Read before writing. Always.
- No silent skips. If a change can't be done as written, pick an alternative, record why,
  carry on.
- Fail loudly, keep moving: record problems in the plan and the summary, take the safest
  path that still finishes the work.
- If the map's areas changed (new folders, moved modules), run the `map` skill in refresh
  mode before completing.

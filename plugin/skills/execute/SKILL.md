---
name: execute
description: Execute one active project end to end - read it, confirm the code matches, implement phase by phase, pass each gate, test, commit each chunk and complete it. Use for a single project; /caddis:build runs this across many.
---

Execute the project named in my message, or the most recently discussed active project.

If I invoked this directly in the main session, hand the project off as in "Run it in the
background" in the `build` skill, with this skill as the agent's job. A background builder
just carries on.

## 1. Load

1. Find the file in `.caddis/projects/active/` and read all of it before writing code.
2. Read `.caddis/caddis.md`. Its Invariants, Commands and Machine limits apply throughout.
3. If it is a master plan (`Type: Master plan`), don't implement it directly: each phase
   becomes its own project via the `project` skill, unless the phase says it is a spike or a
   decision with no feature code.
4. If the project is ambiguous or contradicts the code, the code wins. Fix the project, record it
   under `## Decisions During Build`, and carry on. Never diverge silently.
5. If the project has an Intent, read it. The Summary's Done when checks are part of every
   final gate.

## 2. Explore

Read every file in Changes and Key Reference Files before writing to it. Projects go stale;
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
- **Keep the project true.** When the work departs from Changes (a different file, function
  or approach), update Changes in the same commit as the code, with a line under
  `## Decisions During Build`. The project must describe what was built, not what was guessed.
  Never change the Summary on your own: if what users get must differ, record it and say so
  in the final summary for the product owner.

## 4. Gate each phase

1. Walk the phase's gate and the project's Verification steps that apply. Report each as
   passed, failed or skipped with the reason. Fix root causes.
2. If the project has Tests, write them with the `tests` skill. Run the full suite. If a
   pre-existing test fails, decide on purpose whether the test or the change is wrong.
3. Hand the phase to the `gate-verifier` agent: the project path and phase number, nothing
   about what you did. On **FAIL**, fix the root cause and verify again. If it still fails
   after two rounds, record the finding under `## Decisions During Build` and treat the
   gate as failed. On **INCOMPLETE** for a heavy check, run that check yourself. Skip the
   agent for a phase that only changes docs.
4. Mark the phase heading done: `### Phase 2 - <name> - DONE (YYYY-MM-DD)`. Progress tools
   read this marker.
5. Commit the phase with the `commit` skill. Never commit a failing gate. Don't push.

## 5. Complete

Run the `complete` skill, commit that as its own `docs:` commit, and summarise: files
changed, decisions taken, deviations from the project and why, anything skipped, follow-ups.

## Rules

- Read before writing. Always.
- No silent skips. If a change can't be done as written, pick an alternative, record why,
  carry on.
- Fail loudly, keep moving: record problems in the project and the summary, take the safest
  path that still finishes the work.
- If the map's areas changed (new folders, moved modules), run the `map` skill in refresh
  mode before completing.

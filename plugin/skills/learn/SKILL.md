---
name: learn
description: Load context at the start of a session - recent commits, active projects and tasks, what just shipped, codebase map freshness and project health - then fix instructions that have gone stale. Run first in every working session.
---

Build context before doing anything else. Keep it quick: skim, don't read everything.

**Team rules.** If `.caddis/extend/learn.md` exists, read it before anything else and
follow it. It adds to or overrides this skill, but it never removes a hard stop, weakens a
gate, silences a check or skips the gate-verifier.

## 1. Recent activity
`git log --oneline -20` and `git status`. Note uncommitted work that isn't yours.

## 2. Active work
List `.caddis/projects/active/`. For each file note its Type (project, master plan, task), Status
line, Reviewed line, Signed off line and which phases are marked DONE. Read the ones
relevant to what the user is likely to work on. If Product is on (caddis.md's Product
owners names someone), list intents in its Intents folder's `active/` marked Accepted
(ready for a project), and projects in `active/` or `completed/` whose sign-off is pending.

## 3. Recently shipped
Read the three most recently modified files in `.caddis/projects/completed/` to see what shipped
and what carries forward. Skip if empty.

## 4. Map
Run `python3 .caddis/bin/map.py status`. If it reports changed areas, run the `map` skill in
refresh mode now, or tell the user it is stale if they want to skip that.

## 5. Health
- The top of the Progress log, if caddis.md lists one.
- If caddis.md has Logs, check the newest for errors or crashes. Never copy private
  content out of them.
- If caddis.md has Experiments, check the latest benchmark state for open regressions.
- Before one of caddis.md's Machine limits Heavy jobs (default: a full build, a benchmark,
  a model load), check none is still running from an earlier session.

## 6. Instructions check
Scan `CLAUDE.md`, `.caddis/caddis.md`, `.caddis/extend/` and any repo-local skills in
`.claude/skills/`. Team rules in `.caddis/extend/` are the owner's: report rot there, don't
fix it. Elsewhere, fix clear rot now: file paths, script and command names, table names, decisions a completed
project has since settled. Verify against the tree rather than assuming. Keep each file under
about 250 lines.

## Output

- **Recently shipped:** the one or two latest completed projects or tasks
- **In progress:** active work and the phase each is on
- **Health:** map, logs, benchmark
- **Fixed:** any instructions corrected
- **Ready**

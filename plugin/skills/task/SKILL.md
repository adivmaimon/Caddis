---
name: task
description: Handle a small, low-risk change end to end - write a short task file in .caddis/projects/active/, make the change, verify, move it to completed and commit. Use when the user asks to create a task, make a quick fix or a small change. Escalates to /caddis:project if the work turns out bigger or riskier.
---

A task is a project with less ceremony: a short record, then the work, in one go.

**Team rules.** If `.caddis/extend/task.md` exists, read it before anything else and follow
it. It adds to or overrides this skill, but it never removes a hard stop, weakens a gate,
silences a check or skips the gate-verifier.

**Too small for a task:** a typo, a copy or config value, a dependency bump with no
behaviour change, a comment or docs fix. Skip the task file: make the change, run the
relevant checks and commit with the `commit` skill, no Caddis trailer. Say so in one line.

## 1. Qualify

Read `.caddis/caddis.md`. It is a task only if **all** hold:
- About 3 files or fewer, in one layer
- Nothing on the Risk list (migrations, auth, payments, secrets, data deletion, public
  API or format changes, new runtime dependencies, anything repo-specific listed there)
- No Invariant touched
- No experiment needed: the right answer is not in doubt
- One commit can revert it

If any fails, say which, and follow the `project` skill instead. If one fails partway
through the work, stop, record what was found in the task file, and convert it to a
project: rename to `project-<name>.md`, fill the missing sections, leave it in `active/`.

## 2. Write the task

`.caddis/projects/active/task-<kebab-name>.md`, 15 to 30 lines:

```markdown
# <Title>

**Status:** In progress
**Type:** Task

## Goal
One sentence.

## Change
- `path/to/file` - what changes (function, line)

## Verify
- The command or check that proves it works

## Summary
One or two plain-language bullets for a non-developer.
```

If caddis.md's Plans section is set, its Tasks line decides the ending: `sections` means the
Required sections in their format, in place of `## Summary` unless Keep Summary is yes or
Product is on; `silent` means no Summary and the
Silent marker where it says.

Use `.caddis/map/STRUCTURE.md` and `python3 .caddis/bin/map.py uses <file>` to confirm nothing else depends on
what changes. If the user only wants it logged, stop here with `**Status:** Pending`. Running this skill
later on that task file picks up at step 3.

## 3. Do it

- Read every file before editing it. Grep before adding anything new; reuse first.
- Make the change. Run the checks from caddis.md's Commands (lint, typecheck, the relevant
  tests). Add or update a test when the change is logic, not copy or styling.
- Fix root causes. Never silence a check.

## 4. Close

- Append `## Outcome`: one or two lines on what was done, and anything unexpected. Check the
  ending from step 2 still matches what was done.
- Set `**Status:** Complete` and move the file to `.caddis/projects/completed/`.
- Use `git mv` when `.caddis/` is tracked, plain `mv` when it is gitignored.
- Commit the change and the task file together with the `commit` skill, with the
  `Caddis-Task: task-<name>` trailer.
- Report in two lines: what changed, the commit hash.

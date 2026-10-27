---
name: commit
description: Commit the working tree at the end of a logical chunk of work - a phase gate passed, a fix verified, a task done, a plan added or completed - staging only that chunk, with a conventional message.
---

Commit this chunk's changes with a clear message, following the Commits section of
`.caddis/caddis.md`.

## Steps

1. **Confirm it is a real checkpoint:** a phase gate passed, a fix verified, a refactor
   wrapped, a task done, a plan added (its own `docs:` commit) or completed. Not mid-task,
   not after a read-only turn, never several chunks in one commit. Checks green first.
2. **Survey:** `git status` and `git diff --stat`.
3. **Stage only this chunk's paths** with targeted `git add <paths>`. Never `git add -A`.
   If unrelated edits share a file, write only your hunks to a patch and
   `git apply --cached <patch>`; mention the rest in the report.
4. **Write the message:** `<type>(<scope>): <subject>`, a blank line, then the body.
   - Types and scopes from caddis.md. Subject within caddis.md's Subject length (72
     characters if unset), imperative, no full stop.
   - Body: why, not what. Add `Project: <path>` or `Task: <path>` when it belongs to one.
   - Trailers only as caddis.md allows.
5. `git commit -m "<subject>" -m "<body>"`. Don't push.
6. Report the hash and subject, plus any follow-up that should be its own commit.

## When not to commit

- Changes the owner made and didn't ask you to commit: leave them unstaged and mention them.
- Checks failing, mid-task, or after a read-only turn such as an evaluation.
- During a merge, rebase or cherry-pick.
- When the user gives a message, use theirs.

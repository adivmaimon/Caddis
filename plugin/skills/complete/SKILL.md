---
name: complete
description: Mark a project or task done - append an outcome record, set its status, move it from .caddis/projects/active/ to .caddis/projects/completed/ and update the progress log.
---

Mark the project named in my message complete by moving it from `.caddis/projects/active/` to
`.caddis/projects/completed/`.

**Team rules.** If `.caddis/extend/complete.md` exists, read it before anything else and
follow it. It adds to or overrides this skill, but it never removes a hard stop, weakens a
gate, silences a check or skips the gate-verifier.

## Steps

1. Find the matching file in `.caddis/projects/active/`.
2. Check its Verification was actually worked through, and that it ends right:
   - A plain-language `## Summary` a non-developer can read, unless Required sections
     replace it (the rule in the `project` skill). Rewrite it if missing or too technical:
     bullets, one change each. Each Done when check in it was met, or the outcome record
     says why not.
   - Plans config: every Required section, in its exact format and heading level, unless
     the file carries the Silent marker. Tasks follow the Tasks line. Write or repair what
     is missing or malformed, and apply the Other rules.
3. Append an outcome record. Never strip the original project.
   - **`## What Was Built`** - factual and concrete, no marketing language.
   - **`## Key Files`** - paths from the repo root.
   - **`## Benchmark Delta`** - if the project had an Experiment or touched anything the
     benchmark measures: baseline run, new run, what moved.
   - **`## Decisions Recorded`** - if it settled an open or proposed decision: what was
     decided, the evidence, and confirmation the Architecture doc and caddis.md were updated
     in the same change.
   - **`## Lessons Learned`** - optional, encouraged.
4. Set the status line to `**Status:** Complete` (or `**Status:** Not adopted` when an
   experiment found no winner).
5. Move the file: `git mv` when `.caddis/` is tracked, plain `mv` when it is gitignored.
   The folder is the source of truth for completion.
6. If caddis.md lists a Progress log, add a one-paragraph entry at its top.
7. If the project's `**Signed off:**` is still pending, leave its intent as it is and say
   so: the `review` skill finishes this step when the owner signs off. Otherwise, if the
   project has an Intent file and this project delivered all of it, set the intent's
   `**Status:** Done (project-<name>)` and move it from the Intents folder's `active/` to
   `completed/`, the same way as step 5. If the Intent is a ticket and caddis.md's Sign-off
   is `tracker comment`, post a short comment there: what shipped, in Summary language, and
   any Done when check that changed.
8. Confirm the new path in one or two sentences. Next is usually the `commit` skill.

## When not to complete

- Partial, deferred, on hold or blocked: leave it in `active/` and update the Status line,
  e.g. `**Status:** Blocked - needs a signing key`.
- Abandoned: ask the owner whether to delete it or keep it in `completed/` with
  `**Status:** Cancelled` and a line on why, plus the Silent marker if one is defined.
  Don't invent new folders.
- Master plans move only when every phase is done. Until then keep the Status line current.

`completed/` is plain-text history. Write it for the next person who reads it.

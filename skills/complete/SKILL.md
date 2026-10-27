---
name: complete
description: Mark a plan or task done - append an outcome record, set its status, move it from .caddis/active/ to .caddis/completed/ and update the progress log.
---

Mark the plan named in my message complete by moving it from `.caddis/active/` to
`.caddis/completed/`.

## Steps

1. Find the matching file in `.caddis/active/`.
2. Check it has a plain-language `## Summary` a non-developer can read, and that its
   Verification was actually worked through. Rewrite the Summary if it is missing or too
   technical: bullets, one change each.
3. Append an outcome record. Never strip the original plan.
   - **`## What Was Built`** - factual and concrete, no marketing language.
   - **`## Key Files`** - paths from the repo root.
   - **`## Benchmark Delta`** - if the plan had an Experiment or touched anything the
     benchmark measures: baseline run, new run, what moved.
   - **`## Decisions Recorded`** - if it settled an open or proposed decision: what was
     decided, the evidence, and confirmation the Architecture doc and caddis.md were updated
     in the same change.
   - **`## Lessons Learned`** - optional, encouraged.
4. Set the status line to `**Status:** Complete` (or `**Status:** Not adopted` when an
   experiment found no winner).
5. Move the file. The folder is the source of truth for completion.
6. If caddis.md lists a Progress log, add a one-paragraph entry at its top.
7. Confirm the new path in one or two sentences. Next is usually the `commit` skill.

## When not to complete

- Partial, deferred, on hold or blocked: leave it in `active/` and update the Status line,
  e.g. `**Status:** Blocked - needs a signing key`.
- Abandoned: ask the owner whether to delete it or keep it in `completed/` with
  `**Status:** Cancelled` and a line on why. Don't invent new folders.
- Master plans move only when every phase is done. Until then keep the Status line current.

`completed/` is plain-text history. Write it for the next person who reads it.

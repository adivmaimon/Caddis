<!-- caddis:start -->
## Working here (Caddis)

- **Read first:** `.caddis/caddis.md` (commands, invariants, risk, hard stops) and
  `.caddis/map/STRUCTURE.md` (what lives where). Run `/caddis:learn` at the start of a
  session.
- **Work lives in** `.caddis/projects/active/` and moves to `.caddis/projects/completed/` when done:
  `project-*.md` for planned work, `task-*.md` for small changes. Product intents live in
  `.caddis/intents/` or the tracker.

| When | Use |
| --- | --- |
| Start of a session | `/caddis:learn` |
| A product owner's request | `/caddis:intent` (or start from the ticket) |
| Is this a good idea? | `/caddis:evaluate` |
| Small, low-risk change | `/caddis:task` |
| Anything bigger | `/caddis:project <intent or ticket>`, then `/caddis:review`, then `/caddis:build` |
| Build one plan | `/caddis:execute` |
| Tests for a change | `/caddis:tests` |
| Commit a finished chunk | `/caddis:commit` |
| Map stale or missing | `/caddis:map` |
| Monthly | `/caddis:maintenance` |
<!-- caddis:end -->

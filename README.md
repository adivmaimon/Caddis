<p align="center"><img src="docs/caddis-logo.svg" alt="Caddis" width="420"></p>

<p align="center">A plan-first workflow for Claude Code that fits itself to your codebase.</p>

![A Caddis task: a small change recorded, made, checked and committed in one go](docs/demo.gif)

Caddisfly larvae build their case from whatever is around them: sand, twigs, shell. Caddis
does the same with your repo. One `/caddis:init` reads your codebase and writes down how it
actually works (the commands, the rules, the risky parts, where things live), and every
skill works from that.

What you get:

- **Plans before code.** Evaluate an idea, write a plan, review every plan in one sitting,
  then let the build run unattended. It decides and records instead of asking, and only
  stops for things you'd want to approve: publishing, spending money, secrets, deleting
  outside the repo.
- **A light path for small work.** A one-line fix doesn't need a 100-line plan. `/caddis:task`
  writes a short record, makes the change, verifies it and commits, in one go. It escalates
  to a full plan if the work turns out risky.
- **A codebase map Claude can trust.** A script builds the import graph from real imports
  (no guessed edges), and Claude writes a short human map on top: what lives where, entry
  points, hubs, the main flows, where new things go. A session-start hook says when the
  map has gone stale.
- **History you can read.** Every plan and task stays in `.caddis/projects/completed/` with what was
  built, the decisions taken and what was learned.

## Install

In Claude Code:

```
/plugin marketplace add adivmaimon/caddis
/plugin install caddis@caddis
```

Or from your shell, in one step:

```
claude plugin install caddis --marketplace adivmaimon/caddis
```

In the VS Code extension, use `/plugins` (or the shell command above).

Then, in your repo:

```
/caddis:init
```

Init scans the repo, builds the map, writes `.caddis/caddis.md`, asks you a handful of
questions in one batch (your invariants, anything it had to guess), and commits the setup.

Requirements: Claude Code with plugin support, git, Python 3.8+ (for the map script, no
packages needed).

## The workflow

| When | Skill |
| --- | --- |
| Start of a session | `/caddis:learn` loads recent commits, active plans, map freshness and health |
| Is this a good idea? | `/caddis:evaluate` gives a verdict, impact per layer, risk, alternatives |
| Small, low-risk change | `/caddis:task` records it, does it, verifies it, commits it |
| Anything bigger | `/caddis:project` writes a plan to `.caddis/projects/active/` |
| Before building | `/caddis:review` checks every plan, asks you everything at once, marks them Reviewed |
| Build | `/caddis:build` runs every reviewed plan end to end, unattended |
| Build one plan | `/caddis:execute` |
| Tests | `/caddis:tests` |
| Commit a chunk | `/caddis:commit` stages only that chunk, conventional message |
| Done | `/caddis:complete` adds the outcome record and moves it to `completed/` |
| Map | `/caddis:map` builds or refreshes the codebase map |
| Monthly | `/caddis:maintenance` runs the full audit, with a running log |

The usual loop: **evaluate, project, review, build.** Small things: **task.**

### Task or project?

A task must meet all of these, or it's a project:
- about 3 files or fewer, in one layer
- nothing on the Risk list (migrations, auth, payments, secrets, data deletion, public API
  changes, new dependencies, plus whatever your repo adds)
- no invariant touched
- no experiment needed
- one commit can revert it

`/caddis:project` sends qualifying work to the task path, and a task that turns out risky
becomes a project.

## What init creates

```
.caddis/
  caddis.md              everything specific to this repo: commands, stack, layers,
                         invariants, risk, docs, commit style, tests, hard stops
  projects/active/       plans and tasks in progress
  projects/completed/    finished plans and tasks, with outcome records
  map/STRUCTURE.md       the human map (committed)
  map/graph.json         the import graph (cache, gitignored, rebuilt on demand)
  bin/map.py             the map script, so the repo works without the plugin
CLAUDE.md                a short Caddis block pointing at the above
.claude/settings.json    permissions merged in: Caddis skills and your commands
                         allowed, git push and sudo denied
.claude/skills/          repo-specific skills, only where your repo needs one
                         (release, migrations, bench, logs)
```

**Why the config file?** The skills stay generic so you can upgrade Caddis without merge
conflicts. Everything about your repo lives in one file you can read and edit.

**Already have `.claude/projects/active` and `completed`?** Init offers to move them into
`.caddis/projects/` with `git mv`.

## The map

```
python3 .caddis/bin/map.py build            # graph.json + summary.md
python3 .caddis/bin/map.py status           # is STRUCTURE.md stale? which areas changed?
python3 .caddis/bin/map.py uses <file>      # what depends on this (--depth 2 for transitive)
python3 .caddis/bin/map.py deps <file>      # what this imports
python3 .caddis/bin/map.py area <dir>       # files in an area with in and out degree
python3 .caddis/bin/map.py orphans          # files nothing imports: entry points or dead code
```

Resolves imports for TypeScript and JavaScript (tsconfig paths, `@/` aliases, React Native
platform files, Vue, Svelte), Python, Go, Rust, PHP (PSR-4), Ruby, Java and Kotlin, C and
Objective-C, Dart, and CSS, SCSS and Less. Swift and C# appear as files without edges.
Imports it can't resolve are counted, not guessed, and listed in `summary.md`.

Tested on ten real codebases from 30 to 1,300 source files: under two seconds each.

## Plan format

Plans are plain markdown with a few lines tools can read:

```markdown
# Title

**Status:** Pending
**Type:** Project
**Reviewed:** 2026-10-27

### Phase 1 - The engine - DONE (2026-10-28)
### Phase 2 - The UI
```

[Monty](https://github.com/adivmaimon/monty) reads these to show plan progress in VS Code and
the Mac menu bar.

## Customising

- Edit `.caddis/caddis.md` directly. Re-run `/caddis:init` any time: it merges, and shows
  you a diff before changing what you wrote.
- Add your own skills in `.claude/skills/` and list them under Local skills in caddis.md so
  Caddis skills know when to call them.

## Contributing

Run the map tests with `python3 -m unittest discover tests`. Skills must stay generic:
anything about a specific repo belongs in that repo's `caddis.md`.

## License

MIT

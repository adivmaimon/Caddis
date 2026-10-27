# Caddis

Plans, tasks and a codebase map for Claude Code, set up from your own repo.

A caddisfly larva builds its case from whatever is nearby: sand, twigs, bits of shell.
`/caddis:init` does the same with a repo. It reads the code, CI, docs and git history and
writes `.caddis/caddis.md`: the commands, the rules that must never break, what counts as
risky, the commit style. Every Caddis skill reads that file, so the skills stay generic and
the repo-specific facts live in one place you can edit.

- **Projects.** Evaluate an idea, write a plan, review all open plans in one pass, then build
  them unattended. The build records its decisions instead of asking, and stops only for
  publishing, spending money, secrets, or deleting outside the repo.
- **Tasks.** Small changes skip the plan. `/caddis:task` writes a short task file, makes the
  change, runs the checks and commits. If the work turns out risky, it becomes a project.
- **The map.** A script builds the import graph from the imports in your code. Claude writes
  `STRUCTURE.md` on top of it: areas, entry points, the most-imported files, the main flows,
  where new code goes. A hook at session start says when it is out of date.

Finished plans and tasks stay in `.caddis/projects/completed/` with what was built and why.

## Install

```
claude plugin install caddis --marketplace adivmaimon/caddis
```

Or inside Claude Code: `/plugin marketplace add adivmaimon/caddis`, then
`/plugin install caddis@caddis`. In the VS Code extension the command is `/plugins`.

Then, in your repo:

```
/caddis:init
```

Init builds the map, writes `.caddis/caddis.md`, asks its questions in one batch (your
rules, anything it had to guess) and commits.

Needs Claude Code with plugin support, git, and Python 3.8+ for the map script.

## Skills

| When | Skill |
| --- | --- |
| Start of a session | `/caddis:learn`: recent commits, open plans, map and log health |
| Is this worth doing? | `/caddis:evaluate`: verdict, impact per layer, risk, alternatives |
| A small change | `/caddis:task` |
| Anything bigger | `/caddis:project`: a plan in `.caddis/projects/active/` |
| Before building | `/caddis:review`: checks every plan, asks you everything at once |
| Build | `/caddis:build`: runs every reviewed plan, unattended |
| Build one plan | `/caddis:execute` |
| Tests | `/caddis:tests` |
| Commit | `/caddis:commit`: stages only this chunk of work |
| Done | `/caddis:complete`: adds the outcome and moves it to `completed/` |
| Map | `/caddis:map` |
| Monthly | `/caddis:maintenance`: full audit, with a log carried between runs |

You can also ask in plain words ("create a task to...", "write a plan for..."). Naming the
skill is more reliable.

A change is a task only if all of these hold, otherwise it is a project:
- about 3 files or fewer, in one layer
- nothing on the Risk list in `caddis.md`
- no rule from `caddis.md` touched
- no experiment needed to pick the approach
- one commit can revert it

Full docs, the map commands and the plan format: https://github.com/adivmaimon/caddis

[MIT](LICENSE). Made by [Adiv Maimon](https://adivmaimon.com).

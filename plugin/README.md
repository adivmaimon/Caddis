# Caddis

Projects, tasks and a codebase map for Claude Code, set up from your own repo.

A caddisfly larva builds its case from whatever is nearby: sand, twigs, bits of shell.
`/caddis:init` does the same with a repo. It reads the code, CI, docs and git history and
writes `.caddis/caddis.md`: the commands, the rules that must never break, what counts as
risky, the commit style. Every Caddis skill reads that file, so the skills stay generic and
the repo-specific facts live in one place you can edit.

- **Projects.** Write up a piece of work, review it once, then let Claude build it
  unattended. The build records its decisions instead of asking.
- **Tasks.** Small changes skip the ceremony: a short task file, the change, the checks, a
  commit. Typos and bumps skip Caddis entirely.
- **Intents.** Product owners say what they want in product terms, then sign off one plain
  Summary. They're never asked a technical question.
- **The map.** An import graph of your code, plus a short guide to what lives where. A hook
  says when it is out of date.

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
rules, anything it had to guess, how your team works) and commits.

Needs Claude Code with plugin support, git, and Python 3.8+ for the map script.

## How work flows

Small changes are tasks. Anything bigger is a project: write it with `/caddis:project`,
check it with `/caddis:review`, then `/caddis:build` runs it unattended, one gated commit
per phase. It stops only for the hard stops in `caddis.md`.

A change is a task only if all of these hold, otherwise it is a project:
- about 3 files or fewer, in one layer
- nothing on the Risk list in `caddis.md`
- no rule from `caddis.md` touched
- no experiment needed to pick the approach
- one commit can revert it

## Skills

| When | Skill |
| --- | --- |
| Start of a session | `/caddis:learn`: recent commits, open projects, map and log health |
| A product owner's request | `/caddis:intent`: problem, outcome, done when, in a file or a ticket |
| Is this worth doing? | `/caddis:evaluate`: verdict, impact per layer, risk, alternatives |
| A small change | `/caddis:task` |
| Anything bigger | `/caddis:project`, from an intent or ticket if there is one |
| Before building | `/caddis:review`: checks projects, asks everything at once, sends the Summary for sign-off |
| Build | `/caddis:build`: runs every reviewed project, unattended |
| Build one project | `/caddis:execute` |
| Tests | `/caddis:tests` |
| Commit | `/caddis:commit`: stages only this chunk of work |
| Done | `/caddis:complete`: adds the outcome and moves it to `completed/` (build does this for you) |
| Map | `/caddis:map` |
| Monthly | `/caddis:maintenance`: full audit, with a log carried between runs |
| Set up or refresh | `/caddis:init` |
| Change how Caddis works here | `/caddis:config`: settings and team rules, from plain words |
| Set up or refresh | `/caddis:init` |

You can also ask in plain words ("create a task to...", "create a project for..."). Naming
the skill is more reliable. With no project named, review and build work on the projects
your branch added, so teammates' work is left alone.

## Adapting Caddis

Run `/caddis:config` and say what you want in plain words. Common changes are switches in
`caddis.md` (pause after each phase, skip unreviewed projects, wait for sign-off). Anything
else becomes a team rule in `.caddis/extend/<skill>.md`, which that skill reads first and
follows. A team rule can add or change steps and add hard stops. It can never remove a hard stop,
weaken a gate, silence a check or skip the gate-verifier.

Updates replace the plugin, never your repo's config or team rules. When an update adds
settings, a line at session start says so and `/caddis:config` shows them.

Full docs, diagrams, the map commands and the project format:
https://github.com/adivmaimon/caddis

[MIT](LICENSE). Made by [Adiv Maimon](https://adivmaimon.com).

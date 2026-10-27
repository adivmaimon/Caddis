---
name: init
description: Set up Caddis in a repo - scan the codebase, build the map, write .caddis/caddis.md with this repo's commands, invariants, risks and conventions, add repo-specific skills where needed, wire settings and CLAUDE.md, and migrate any existing .claude/projects plans. Safe to re-run to refresh the config.
---

Set up Caddis in the current repo so every Caddis skill knows how this codebase works.
The skills stay generic; everything specific goes in `.caddis/caddis.md`.

This skill's `templates/` folder holds `caddis.md` and `claude-md-block.md`. The map skill's
`scripts/` folder holds `map.py`.

## 1. Preflight

- Confirm this is the repo root and a git repo. If it isn't git, say so; Caddis works but
  staleness checks and the commit skill won't.
- If `.caddis/caddis.md` exists, this is a **re-init**: do every step, but propose changes
  to the existing config as a diff and keep everything the owner wrote.
- Note what's already there: `CLAUDE.md`, `AGENTS.md`, `.claude/skills/`, `.claude/agents/`,
  `.claude/settings.json`, and any older plan folders (`.claude/projects/`, `plans/`,
  `docs/plans/`).
- Check the working tree is clean. If not, list what's uncommitted and leave it alone.

## 2. Scan

Gather evidence. Prefer what the repo does over what its docs say.

- **Commands:** `package.json` scripts, `Makefile`, `justfile`, `pyproject.toml`,
  `composer.json` scripts, `Cargo.toml`, `go.mod`, task runners. **CI workflows are the most
  reliable source**: the commands CI runs are the ones that work.
- **Stack and layers:** manifests, top-level folders, framework config files.
- **Tests:** test folders per layer, frameworks, config, shared helpers and fixtures. Run
  the test command once if it is fast and safe, to confirm it works.
- **Rules:** `CLAUDE.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/`, and any
  existing skills. Collect stated rules, constraints and "never do X" lines. These are
  candidate Invariants.
- **Commits:** `git log --format='%s%n%b' -100`. Infer the style, the types and scopes in
  use, and the trailer policy.
- **Risk surface:** migrations folders, auth, payments, secrets handling, public APIs,
  deploy scripts, anything that sends data off the machine.
- **Docs:** an architecture or decisions doc, a progress log or changelog, brand or copy
  rules.
- **Logs and benchmarks:** where runtime logs go; any benchmark or eval harness.

## 3. Map

Run the `map` skill in full mode. Its area names feed the commit scopes and the Layers.

## 4. Write `.caddis/caddis.md`

Start from `templates/caddis.md`. Fill every section from the evidence, citing where each
item came from when it isn't obvious. Rules:
- **Commands:** exact, copy-pasteable, verified where safe.
- **Invariants:** only rules the repo already states or clearly enforces in code. Never
  invent one. If none are stated, leave the section with a comment and ask the owner.
- **Risk:** keep the defaults, add what this repo makes risky.
- **Hard stops:** keep the defaults, add repo-specific ones (e.g. a deploy script).
- **Experiments:** fill only if a benchmark or eval harness exists.
- Mark anything uncertain `(guess - confirm)`.
- Delete sections that clearly don't apply. Keep it under about 200 lines.

## 5. Ask once

Collect everything that needs the owner and ask in **one batch**, each with your
recommended answer: the Invariants, anything marked `(guess - confirm)`, extra hard stops,
whether to turn on Experiments, the commit trailer policy, and any migration choices from
step 7. Use the question tool if there is one. If nobody answers, take the recommendations,
mark them `(default, YYYY-MM-DD)`, and carry on.

## 6. Repo-specific skills

Caddis's own skills are generic. Where this repo has a recurring workflow they don't cover,
write a short repo-local skill in `.claude/skills/<name>/SKILL.md` and list it under Local
skills in caddis.md. Only with clear evidence. Typical cases:
- **release** - there's a release, deploy or publish process (scripts, CI release jobs)
- **migrations** - there's a schema and a migrations folder
- **bench** - there's a benchmark or eval harness
- **logs** - the app writes logs worth reading after a run

Each is under about 60 lines, uses the exact commands and paths, and says when Caddis
skills should call it. If the repo already has skills, keep them. Where an existing skill
duplicates a Caddis one (an older `commit`, `project`, `execute`...), move anything
repo-specific from it into caddis.md and ask before removing it.

## 7. Migrate existing plans

If `.claude/projects/active` and `completed` (or similar) exist, offer to move them:
`active/*` to `.caddis/active/`, `completed/*` to `.caddis/completed/`, other buckets
(cancelled, parked) to `completed/` with their Status line saying so. Use `git mv` so
history follows. Rename files that don't start `project-` or `task-` only if the owner
agrees.

## 8. Wire it up

- **Folders:** `.caddis/active/.gitkeep` and `.caddis/completed/.gitkeep`.
- **CLAUDE.md:** add `templates/claude-md-block.md` between its markers near the top,
  or replace the existing block on re-init. Create CLAUDE.md if missing. Don't move other
  content without asking; if CLAUDE.md holds commands or rules that now live in caddis.md,
  suggest trimming it.
- **Settings:** merge into `.claude/settings.json`, never dropping existing entries:
  - `permissions.allow`: `Skill(caddis:*)`, the exact commands from caddis.md,
    `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)`, `Bash(git add *)`,
    `Bash(git commit *)`, `Bash(git mv *)`, `Bash(python3 .caddis/bin/map.py *)`
  - `permissions.deny`: `Bash(git push*)`, `Bash(sudo *)`, plus any deploy or publish
    commands found
  - Never touch `.claude/settings.local.json`.

## 9. Commit and report

Commit everything as `chore(caddis): set up Caddis` with the `commit` skill. Then report in
a few lines: the areas found, the commands, the invariants (and which are defaults), local
skills created, plans migrated, and what to run next (usually `/caddis:learn`, then
`/caddis:task` or `/caddis:project`).

## Rules

- Evidence over assumption. Every command and path in caddis.md exists.
- Never invent invariants, owners or policies.
- Don't change application code.
- Re-running init must be safe: merge, don't overwrite.

---
name: config
description: Change how Caddis works in this repo from a plain-language request - view and update settings in .caddis/caddis.md (workflow switches, hard stops, product, commands) or write team rules in .caddis/extend/ for any Caddis skill or agent. Also brings an older config up to date after a Caddis update, without touching what the owner wrote.
---

Change how Caddis works here, as described in my message. With no message, show the
current setup and ask what to change.

**Team rules.** If `.caddis/extend/config.md` exists, read it before anything else and
follow it. It adds to or overrides this skill, but it never removes a hard stop, weakens a
gate, silences a check or skips the gate-verifier.

## 0. Setup

Read `.caddis/caddis.md`. If it is missing, say so and run the `init` skill instead. Read
every file in `.caddis/extend/`. The names you can extend are the folder names under this
plugin's `skills/` and the file names under its `agents/` (without `.md`), two levels up
from this skill.

## 1. Show

With no request, or when I ask what's set, give a short view:
- **Workflow:** each switch and its value, `(default)` where the line is missing
- **Product:** on or off, and the sign-off route
- **Hard stops:** the repo's additions beyond the defaults
- **Team rules:** each file in `.caddis/extend/` and its rules, one line each
- **New settings:** anything in `templates/caddis.md` (in the `init` skill's folder) that
  this config doesn't have yet, with its default

Then ask what to change, in one question with suggestions.

## 2. Decide where each change goes

- **A line the template already has** (a Workflow switch, a command, the sign-off route,
  a Product owner): edit that line in caddis.md. A switch always beats a team rule.
- **A fact about the repo** (an invariant, a risk, a new hard stop): add it to its section in
  caddis.md. Invariants are numbered; add the next number, never renumber.
- **Anything else about how a skill or agent behaves:** a team rule in
  `.caddis/extend/<name>.md`. Pick the skill where it happens: a rule about commit messages
  goes in `commit`, a rule about every phase in `execute`, a rule about questions at
  review in `review`. If it spans several, write it in each, or in the one that calls the
  others and say so.
- **A new recurring job** (deploy a preview, post to a channel): a repo skill in
  `.claude/skills/<name>/SKILL.md`, listed under Local skills in caddis.md, plus a team
  rule that says when to call it.

If a request can't be placed, ask one question with your suggestion.

## 3. Refuse what breaks the guarantees

- A team rule never removes a hard stop, weakens a gate, silences a check or skips the
  gate-verifier. Say why and offer the nearest safe version.
- Removing a hard stop from caddis.md happens only when I ask for that by name. Say what
  it lets the build do unattended, and confirm once before editing.
- Never edit plugin files. Everything lives in the repo.

## 4. Write

Team rule files look like this. Keep each rule one line, concrete and checkable:

```markdown
# Team rules: build

<!-- Written by /caddis:config. Caddis updates never change this file; edit it by hand
or with /caddis:config. -->

## Before
- Rebase the branch on main. (owner, YYYY-MM-DD)

## Each phase
- Run the `preview-deploy` skill and paste its URL into the project. (owner, YYYY-MM-DD)

## Always
- Never touch anything under `legacy/`. (owner, YYYY-MM-DD)
```

Use only the headings you need: Before, Each phase, After, Always. When a file exists,
add to it; never drop or reword a rule unless I ask. Check the new rule against
caddis.md and the other team rules, and say if two conflict.

Show the change as a diff, apply it when I agree, and commit it with the `commit` skill
as `chore(caddis): <what changed>`, unless `.caddis/` is gitignored.

## 5. Bring an older config up to date

When I ask to update, or the session-start note says Caddis was updated:
1. Compare caddis.md with `templates/caddis.md`, section by section and line by line.
2. List what's new with its default and what it does. Missing lines already behave as
   their default, so adding them is for visibility, not to make them work.
3. Add what I choose, in the template's position, with the template's comments. Never
   change a value, a rule or a comment the owner wrote, and never delete a section.
4. Set the `caddis-config` marker on the file's first line to the plugin version in
   `.claude-plugin/plugin.json`.
5. Commit as above.

## Output

What changed and in which file, in one or two lines, and the commit hash.

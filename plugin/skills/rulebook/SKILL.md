---
name: rulebook
description: Build and keep .caddis/rulebook.md, the short list of working rules agreed with the owner (style, layout, copy, process) that Caddis loads into every session and every agent. Builds it from memory, CLAUDE.md, docs and other .md files; adds a rule when the owner states or corrects one, and retires a rule that no longer holds. Use when the user says "add a rule", "remember to always", "from now on", "that rule is gone", or asks what the rules are.
---

Keep `.caddis/rulebook.md` true and short. Caddis's SessionStart hook prints it into every
session (startup, resume, clear, compact) and every subagent, so a rule written here is not
forgotten. A rule only in memory or a chat is.

**Team rules.** If `.caddis/extend/rulebook.md` exists, read it before anything else and
follow it. It adds to or overrides this skill, but it never removes a hard stop, weakens a
gate, silences a check or skips the gate-verifier.

## What belongs here

- **Rulebook:** how work is done here, rules a reviewer could check in a diff or a reply. "No
  `<style>` blocks in Vue files." "Buttons are text only." "Copy says credits lapse, not
  expire." Rules the owner gave, or corrected you on.
- **Not here:** caddis.md's Invariants (system rules projects cite; the hook prints them
  too), commands, facts about the repo or its hosts ("prod runs PHP 8.3"), one-off
  decisions, how Caddis itself runs (that is `.caddis/extend/`). Facts stay in memory or docs.
- Never copy a rule in twice. If an Invariant already says it, leave it there.

## Format

Start from `templates/rulebook.md` in this skill's folder. Rules are grouped under `##`
headings by area and numbered across the whole file. A number is never reused or
renumbered: projects, reviews and commits cite rules by number. Each rule is one line,
imperative, specific enough to check, ending with its source and date:
`(owner, 2026-11-20)`, `(CLAUDE.md)`, `(memory: styling-in-scss-files)`, `(learned, 2026-11-20)`.
`## Before calling work done` holds the checks that catch a broken rule (a grep, a command,
a screenshot). `## Retired` holds dropped rules with why and when; the hook leaves that
section out, and its only job is to stop a dropped rule coming back from an old doc or
memory. Keep the live part under about 80 lines: merge rules that overlap.

## Build (init, or "build the rulebook")

1. **Sources.** Read, newest first where dates exist:
   - Claude Code memory for this repo: the folders in `~/.claude/projects/` whose name is
     the repo's absolute path, or a subfolder's, with every `/` and `.` turned into `-`.
     Read `MEMORY.md` and every `feedback`-type file.
   - `CLAUDE.md`, `AGENTS.md`, `CLAUDE.local.md`, nested `CLAUDE.md` files, `.claude/rules/`,
     `.cursorrules`, `.github/copilot-instructions.md`, `CONTRIBUTING.md`, and style or
     writing docs that caddis.md's Docs names.
   - An existing hand-made rulebook (`.claude/rulebook.md`, `RULES.md`...), and any
     SessionStart hook in `.claude/settings.json` that prints one.
2. **Pick.** Keep each "always", "never", "only" and correction that fits What belongs here.
   Where sources disagree, the newest owner statement wins; the losing one goes to Retired
   if it was ever a live rule. Where a doc and the code disagree, the code wins only if the
   owner never said otherwise.
3. **Write** the file. On a rebuild, keep every number and every owner-sourced rule unless
   the owner retires it; show the change as a diff.
4. **Migrate.** If a hand-made rulebook is loaded by a settings hook, offer to remove that
   hook (Caddis now loads the file) and the old file, with `git mv` if it is the same rules.
   Leave the owner's memory files alone.
5. **Ask once** with the init batch, or alone: each rule you were unsure of, each conflict.

## Add, change or retire (any time)

When the owner states a rule ("from now on", "never", "always"), corrects the same thing a
second way, or says a rule no longer holds, edit the rulebook **in the same turn**, before
going on with the work, then say so in one line: `Rulebook: added 18. Buttons are text only.`
- **New:** next number, under the right heading, source `(owner, date)`.
- **Changed:** edit the line in place, keep its number, update the date.
- **Retired:** move the line to Retired with `- <why> (owner, date)`.
- **Learned** (you inferred it, nobody said it): add it marked `(learned, date)` only when
  the evidence is strong, say so in one line, and drop it if the owner objects.
- If a check can catch it, add or extend a line under Before calling work done.
- If you also save it to memory, the rulebook comes first.

Commit it with the `commit` skill as `docs(rulebook): <what changed>`, with the work it
came with or on its own.

## Check (learn, maintenance, or "what are the rules")

- Memory feedback files newer than the rulebook (`find <memory> -newer .caddis/rulebook.md`)
  hold rules not yet in it: list them and offer to fold them in.
- Rules naming a path, component, class or command that no longer exists: fix the name, or
  offer to retire the rule.
- Over about 80 live lines: propose merges.
- Asked what the rules are: list the headings and numbers, one line each.

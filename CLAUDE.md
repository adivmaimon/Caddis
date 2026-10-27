# Caddis - working on Caddis itself

Caddis is a Claude Code plugin: generic workflow skills plus a codebase map script. This file
is for developing Caddis, not for repos that use it.

## Layout

- `.claude-plugin/` - plugin and marketplace manifests. Bump `version` in `plugin.json` on
  every release.
- `skills/<name>/SKILL.md` - one skill each, invoked as `/caddis:<name>`.
- `skills/init/templates/` - `caddis.md` (the per-repo config) and the CLAUDE.md block.
- `skills/map/scripts/map.py` - the map script. Init copies it to `.caddis/bin/map.py` in
  each repo; bump `VERSION` in it on every change so repos pick up the new copy.
- `hooks/hooks.json` - SessionStart: report a stale map. Must stay silent and exit 0 when
  there's nothing to say.
- `tests/` - map.py tests, stdlib unittest.

## Rules

1. **Skills are generic.** Nothing about a specific repo, stack, product or person. If a
   skill needs a repo fact, it reads it from `.caddis/caddis.md`; if the config has no
   section for it, add one to the template.
2. **Skills say when, the config says what.** Commands, paths, invariants, risk and stops
   live in the config, never hardcoded in a skill.
3. **map.py stays standard library only**, Python 3.8+, and never invents an edge. An
   import it can't resolve is counted as unresolved.
4. **Plan format is a contract.** `**Status:**`, `**Type:**`, `**Reviewed:**` lines and
   `### Phase N - <name>` headings with ` - DONE (YYYY-MM-DD)` markers. Other tools (Monty)
   parse them. Don't change them without a major version bump.
5. Keep each SKILL.md under about 150 lines. Plain, direct language. No em dashes.
6. Test map.py changes on real repos of different stacks, not only the fixtures.

## Commands

| Purpose | Command |
| --- | --- |
| Tests | `python3 -m unittest discover tests` |
| Map a repo without touching it | `python3 skills/map/scripts/map.py --root <repo> --out /tmp/map build` |

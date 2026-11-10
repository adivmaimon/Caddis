# Contributing to Caddis

Caddis is a Claude Code plugin: generic workflow skills plus a codebase map script. This file
is for developing Caddis, not for repos that use it.

## Layout

- `.claude-plugin/marketplace.json` - the marketplace, pointing at `plugin/`.
- `plugin/` - everything that gets installed, and nothing else: the plugin directory
  scans every file in it. Docs, images and tests stay outside.
- `plugin/.claude-plugin/` - `plugin.json` and the listing icon. Bump `version` in
  `plugin.json` on every release.
- `plugin/skills/<name>/SKILL.md` - one skill each, invoked as `/caddis:<name>`.
- `plugin/skills/init/templates/` - `caddis.md` (the per-repo config) and the CLAUDE.md block.
- `plugin/skills/map/scripts/map.py` - the map script. Init copies it to `.caddis/bin/map.py` in
  each repo; bump `VERSION` in it on every change so repos pick up the new copy.
- `plugin/skills/build/scripts/progress.sh` - the build status reporter, run under Monitor.
  It reads project files and git only, so builders need do nothing to be reported on.
- `plugin/agents/` - read-only reviewers the skills hand work to. They get a path, not the
  author's context, and must never edit, run heavy jobs or touch a hard stop.
- `plugin/hooks/` - plain bash scripts, run by literal `${CLAUDE_PLUGIN_ROOT}` paths (the
  directory refuses computed paths). `session-start.sh` reports a stale map, `announce.sh`
  shows the skill badge. Both must stay silent and exit 0 when there's nothing to say.
- `tests/` - map.py and progress.sh tests, stdlib unittest.

## Rules

1. **Skills are generic.** Nothing about a specific repo, stack, product or person. If a
   skill needs a repo fact, it reads it from `.caddis/caddis.md`; if the config has no
   section for it, add one to the template.
2. **Skills say when, the config says what.** Commands, paths, invariants, risk and stops
   live in the config, never hardcoded in a skill.
3. **map.py stays standard library only**, Python 3.8+, and never invents an edge. An
   import it can't resolve is counted as unresolved.
4. **The file formats are a contract.** In projects and tasks: the `**Status:**`,
   `**Type:**`, `**Depends on:**`, `**Intent:**`, `**Reviewed:**` and `**Signed off:**`
   lines, `### Phase N - <name>` headings with ` - DONE (YYYY-MM-DD)` markers, and the
   `Caddis-Plan:` and `Caddis-Task:` trailers. In intents: the `**Status:**` values Draft,
   Accepted, Planned and Done. Other tools (Monty) parse them. Don't change them without a
   major version bump.
5. **Teams adapt Caddis without forking it.** Every skill and agent starts by following
   `.caddis/extend/<name>.md` when it exists, and repo switches live in caddis.md's
   Workflow section. A new skill or agent gets the same Team rules line. Keep the
   extension file names equal to the skill and agent names; renaming one breaks every
   repo that extends it.
6. Keep each SKILL.md under about 150 lines. Plain, direct language. No em dashes.
7. Test map.py changes on real repos of different stacks, not only the fixtures.

## Commands

| Purpose | Command |
| --- | --- |
| Tests | `python3 -m unittest discover tests` |
| Map a repo without touching it | `python3 plugin/skills/map/scripts/map.py --root <repo> --out /tmp/map build` |

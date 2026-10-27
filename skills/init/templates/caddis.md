# Caddis config

> Every Caddis skill reads this file. It holds everything specific to this repo so the
> skills themselves stay generic and can be upgraded. `/caddis:init` writes it; edit it by
> hand whenever something here changes. Leave a section empty, or delete it, when it does
> not apply. Keep the whole file under about 200 lines.

## About

<!-- One paragraph: what this project is, who uses it, what matters most to them. -->

## Owner

<!-- Who makes the calls. Decisions in plans are tagged (owner, YYYY-MM-DD). -->

## Commands

<!-- The exact commands. Skills run these and nothing else for checks. -->

| Purpose | Command |
| --- | --- |
| Everything (lint, types, tests) | |
| Lint | |
| Typecheck | |
| Format check | |
| Tests | |
| Build | |
| Dev server | |
| Benchmark | |

## Stack

<!-- Languages, frameworks, runtimes, where each layer lives. One line each. -->

## Layers

<!-- The parts of the system a change can touch. /evaluate reports impact per layer and
/project phases large work by layer. Example: UI, API, database, background jobs, infra. -->

## Invariants

<!-- Rules that hold on every code path, no exceptions. Plans must say which they touch and
how each is preserved. Example: "Nothing leaves the device without consent." Number them so
plans can cite them. -->

## Risk

Medium or higher, whatever the size:
- Schema or data migrations, or anything that deletes or rewrites stored data
- Auth, permissions, payments, secrets
- Anything that can break an Invariant
- Public API, file format or protocol changes
- New runtime dependencies

<!-- Add what is risky in this repo. -->

## Docs

<!-- Paths. Skills keep these accurate in the same change that makes them stale. -->

| Doc | Path |
| --- | --- |
| Architecture and decisions | |
| Progress log (newest first) | |
| Brand and copy rules | |
| Codebase map | `.caddis/map/STRUCTURE.md` |

## Plans

<!-- Leave empty to keep the default: every plan and task ends in `## Summary`. Fill it when
something reads plan files (a deploy script, a changelog tool) and needs set headings. -->

- Required sections: <!-- each heading and its format, e.g. "`## Release notes`: bullets
  `- <b>Headline</b>. Description.`". These replace `## Summary` unless the next line says
  otherwise. -->
- Keep Summary: <!-- "yes" to write `## Summary` as well; default no -->
- Silent marker: <!-- a line that tells the tool to skip a file, and where it goes, e.g.
  "`**Silent:** true` above the Status line". Silent files carry no required sections. -->
- Tasks: <!-- "sections" (same as plans) or "silent" (the marker instead); default sections -->
- Other rules: <!-- line limits, what a cancelled plan needs, anything else -->

## Commits

- Style: conventional, `<type>(<scope>): <subject>`
- Types: feat, fix, refactor, perf, test, docs, chore, ci
- Scopes: <!-- from the map's areas -->
- Subject length: <!-- default 72 characters -->
- Trailers: <!-- e.g. "none", or "Co-Authored-By allowed" -->

## Tests

<!-- Where tests live per layer, the frameworks, and the priorities in order: what must
never break. Patterns to follow (mocks, fixtures). -->

## Experiments

<!-- Leave empty to turn experiment phases off. When set, plans that change behaviour run
variants against a baseline before building. -->

- Benchmark command:
- Metrics that matter:
- Threshold to adopt:

## Logs

<!-- Where runtime logs live, and what must never be copied out of them. -->

## Reference repos

<!-- Sibling repos to read and port from, with absolute paths and what to take from each. -->

## Machine limits

<!-- e.g. "One heavy job at a time: never run the model beside a release build." -->

## Hard stops

`/caddis:build` runs unattended and stops only for these:
- Publishing anything: push, tag, release, deploy, upload
- Spending money or signing up for a paid service
- Creating, rotating or exposing secrets or signing keys
- Deleting or overwriting anything outside the repo

<!-- Add repo-specific stops. -->

## Local skills

<!-- Repo-specific skills in .claude/skills/ that init created or that already existed,
one line each: name and when Caddis skills should call it. To run one in /caddis:maintenance,
end its line with `Maintenance:` and any ordering note, e.g. "`ui-audit`: screenshot audit.
Maintenance: start first, background, ~50 min." Maintenance runs them and skips its own steps
they cover. -->

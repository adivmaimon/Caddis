<!-- caddis-config: VERSION -->
# Caddis config

> Every Caddis skill reads this file. It holds everything specific to this repo so the
> skills themselves stay generic and can be upgraded. `/caddis:init` writes it; change it with
> `/caddis:config` or by hand. Caddis updates never overwrite it. Leave a section empty, or delete it, when it does
> not apply. Keep the whole file under about 200 lines.

## About

<!-- One paragraph: what this project is, who uses it, what matters most to them. -->

## Owner

<!-- Who makes the calls. Decisions in projects are tagged (owner, YYYY-MM-DD). -->

## Product

<!-- Product is on when Product owners names someone; otherwise leave this section empty.
When on, product owners write intents with /caddis:intent and sign off each project's
Summary; projects built from an intent quote it. Needs `.caddis/` in git. -->

- Product owners: <!-- names. Product decisions are tagged (product, YYYY-MM-DD) -->
- Intents: `.caddis/intents/` <!-- intent files live in its active/ until delivered, then
  completed/ -->
- Tracker: <!-- e.g. "Jira, projects ABC and XYZ, via the Atlassian connector", or none.
  Tickets can be the intent instead of a file -->
- Sign-off: <!-- where the owner approves a project's Summary: "tracker comment" (on the
  intent's ticket) or "PR" (the draft PR for the project's branch). Default: PR. "none"
  turns sign-off off -->
- Writing: <!-- path to plain-language rules for intents and Summaries, e.g. "CLAUDE.md,
  Communication". Default: short sentences, plain words, no jargon -->

## Workflow

<!-- Switches for how this team works. Leave a line out to keep its default. For anything
these don't cover, write `.caddis/extend/<skill>.md`: instructions that add to or override
that skill (see the Caddis README, Adapting Caddis). -->

- Pause after each phase: no <!-- "yes": build and execute stop after every phase commit and
  report. Run /caddis:build again to carry on -->
- Unreviewed projects: review with defaults <!-- or "skip": build runs only projects that
  /caddis:review marked Reviewed -->
- Wait for sign-off: yes <!-- "no": a project builds before the product owner signs off,
  and its intent stays open until they do -->
- Merge by rule: none <!-- files every project touches that the integrator reconciles
  when parallel builds merge, e.g. a version file. Comma-separated paths. Projects that
  share only these still build side by side -->
- Build panel: on <!-- "off": no live panel beside the chat during /caddis:build; progress
  shows on the status line instead. Text reports in the chat are the same either way -->

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
| Dependency audit | |

## Stack

<!-- Languages, frameworks, runtimes, where each layer lives. One line each. -->

## Layers

<!-- The parts of the system a change can touch. /evaluate reports impact per layer and
/project phases large work by layer. Example: UI, API, database, background jobs, infra. -->

## Invariants

<!-- Rules that hold on every code path, no exceptions. Projects must say which they touch and
how each is preserved. Example: "Nothing leaves the device without consent." Number them so
projects can cite them. -->

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

<!-- Leave empty to keep the default: every project and task has a `## Summary`. Fill it when
something reads project files (a deploy script, a changelog tool) and needs set headings. -->

- Required sections: <!-- each heading and its format, e.g. "`## Release notes`: bullets
  `- <b>Headline</b>. Description.`". These replace `## Summary` unless Keep Summary is yes or
  Product is on. -->
- Keep Summary: <!-- "yes" to write `## Summary` as well; default no -->
- Silent marker: <!-- a line that tells the tool to skip a file, and where it goes, e.g.
  "`**Silent:** true` above the Status line". Silent files carry no required sections. -->
- Tasks: <!-- "sections" (same as projects) or "silent" (the marker instead); default sections -->
- Other rules: <!-- line limits, what a cancelled project needs, anything else -->

## Commits

- Style: conventional, `<type>(<scope>): <subject>`
- Types: feat, fix, refactor, perf, test, docs, chore, ci
- Scopes: <!-- from the map's areas -->
- Subject length: <!-- default 72 characters -->
- Trailers: <!-- e.g. "none", or "Co-Authored-By allowed". Caddis always adds its own
  `Caddis-Plan:` or `Caddis-Task:` trailer to commits for a project or task, unless
  .caddis/ is gitignored -->
- `.caddis/` in git: yes <!-- "no" when .caddis/ is gitignored to keep projects private: project
  files are then moved with mv, never staged or force-added, and never named in commits -->

## Tests

<!-- Where tests live per layer, the frameworks, and the priorities in order: what must
never break. Patterns to follow (mocks, fixtures). -->

## Experiments

<!-- Leave empty to turn experiment phases off. When set, projects that change behaviour run
variants against a baseline before building. -->

<!-- Uses the Benchmark command under Commands. -->

- Metrics that matter:
- Threshold to adopt:

## Logs

<!-- Where runtime logs live, and what must never be copied out of them. -->

## Reference repos

<!-- Sibling repos to read and port from, with absolute paths and what to take from each. -->

## Machine limits

<!-- What this machine can run at once. A missing line means its default. Heavy jobs always
run one at a time, never beside each other. -->

- Parallel agents: no cap
- Heavy jobs: full build, benchmark, model load
- Notes:

## Hard stops

`/caddis:build` runs unattended and stops only for these:
- Publishing anything: push, tag, release, deploy, upload
- Spending money or signing up for a paid service
- Creating, rotating or exposing secrets or signing keys
- Deleting or overwriting anything outside the repo
- Destructive commands against any shared database or environment: drop, truncate, reset,
  bulk delete, or migrations anywhere but a local database

<!-- Add repo-specific stops. -->

## Local skills

<!-- Repo-specific skills in .claude/skills/ that init created or that already existed,
one line each: name and when Caddis skills should call it. To run one in /caddis:maintenance,
end its line with `Maintenance:` and any ordering note, e.g. "`ui-audit`: screenshot audit.
Maintenance: start first, background, ~50 min." Maintenance runs them and skips its own steps
they cover. -->

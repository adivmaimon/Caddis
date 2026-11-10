---
name: review
description: Review the active projects before a build - check them against caddis.md, the architecture doc, the code, their intent and each other, fix what can be fixed, ask the owner every technical question in one batch, send the Summary to the product owner for sign-off, and mark each project Reviewed so /caddis:build can run without stopping.
---

Review every project in `.caddis/projects/active/`, or the ones named in my message. The goal is a set
of projects `/caddis:build` can run start to finish without asking anything.

## Steps

1. **Read** `.caddis/caddis.md`, `.caddis/map/STRUCTURE.md`, the Architecture doc and every
   project in scope. Work out the build order from each project's `Depends on` line.
2. **Check each project:**
   - It agrees with caddis.md, the Architecture doc and the other projects. Fix contradictions
     in the project, or in the docs if the project is right.
   - Every file, command and path it names exists, or an earlier project creates it. Verify
     against the tree, not memory.
   - Every phase has a gate a machine can check: a test, a measurement, a file that exists.
   - It names every Invariant it touches and how each holds. No Invariants section means
     none is touched: check that is true.
   - If it has an Intent, it delivers the Outcome and every Done when check, and builds
     nothing under Out of scope. Read the intent file or ticket to check.
   - The Summary reads plainly for a non-developer, per caddis.md's Product Writing rules:
     what changes for users, Done when, and only product questions. Move technical
     content out of it.
   - No empty sections, and no "None" or "Skipped" lines. Delete them.
   - Its Risk level matches caddis.md's Risk list.
   - If caddis.md has Experiments set and the project changes behaviour, it has an Experiment
     phase first with variants, a baseline, real measures and a rule for the winner.
   - Dependencies between projects are explicit and the order respects them.
   - Any user-facing copy follows the Brand doc, if there is one.
   - Every `chart` and `flow` block is valid YAML with the keys and values the `project`
     skill gives: a chart has `title`, `better` (`lower` or `higher`) and `rows` of
     `[label, number]` plus an optional `winner` or `rejected` tag; a flow has `title` and
     `steps`, and every `branch` `from` and `to` names a step. Fix a broken block in place.
   - It carries the sections caddis.md's Plans section requires, in the stated format, or
     the Silent marker, plus the `## Summary` the `project` skill describes.
   Then hand each project to the `plan-reviewer` agent for a fresh read without your context:
   just the project's path, plus the ticket's text when its Intent is a ticket (the agent has
   no tracker tool). Run them one at a time if caddis.md's Machine limits rule out
   parallel agents. Treat its blocking findings as yours to fix; judge its minor ones.
3. **Measure reach.** For each project, run `python3 .caddis/bin/map.py reach <files>` on the
   existing files its Changes list (skip ones it creates). Write the result into its Risk
   section as a `**Reach:**` paragraph, one or two sentences on what the change touches,
   then a table:

   | Area | Files reached | Through a hub |
   | --- | --- | --- |
   | `src/api` | 12 | 9 |

   Name any hubs it touches in the paragraph. With no reach, one line saying so, no table. If the reach and the stated Risk level
   disagree (a wide reach rated low, or a hub change with no Risk note), that is an owner
   question for step 5, with your recommended level. Add each direct importer no test
   reaches to the project's Tests section as a suggested entry.
4. **Fix what you can** directly: stale paths, missing gates, wrong order, vague steps.
5. **Collect every technical question** across all projects, including each project's Open
   Questions. Ask them **once, together**, each with a recommended answer. Ask only what
   changes what gets built; decide the rest and record it. Scope and behaviour questions
   belong to product: move them to the Summary's Questions for product instead.
6. **Write the answers in** as decisions `(owner, YYYY-MM-DD)`. Give every remaining open
   question a default the build will use.
7. **Mark each project** with `**Reviewed:** YYYY-MM-DD` under its Status line.
8. **Product sign-off.** Skip when caddis.md has no Product section, its Sign-off is
   `none`, or the project changes nothing users see. Otherwise send the project's Summary, with
   its Questions for product, where Sign-off says: a comment on the intent's ticket with the
   tracker tool, or the PR that adds the project (tell me to raise it if there isn't one). Add
   `**Signed off:** pending` under the Reviewed line. When the owner approves (I tell you,
   or their reply is on the ticket or PR), set `**Signed off:** <name> YYYY-MM-DD` and write
   their answers in as `(product, YYYY-MM-DD)`. Ask again only if the Summary changes:
   technical changes never need a new sign-off.
9. **Commit** the reviewed projects as one `docs:` commit with the `commit` skill, unless
   `.caddis/` is gitignored.

## Output

- Projects reviewed and what was fixed in each
- Owner decisions and defaults chosen
- Sign-off sent, and to whom, per project
- The build order
- "Ready for /caddis:build", or the one thing blocking it (a pending sign-off counts only
  when caddis.md's Wait for sign-off is yes)

## Rules

- No code. This is the last point the owner is asked anything before the build.
- Don't ask what the docs, the code or a sensible default already answers.

---
name: intent
description: Capture what a product owner wants built, in product terms only - write an intent file in .caddis/intents/active/, or check and complete a ticket in the issue tracker. For product managers and owners; no technical questions. Feeds /caddis:project.
---

Capture the intent described in my message: the problem, the outcome and how we'll know it
works. No solution, no code. This is the product owner's only writing step; Claude writes
the project from it later with the `project` skill.

## 0. Setup

Read `.caddis/caddis.md` if you can reach it, in particular Product. If you can't (no repo
checked out), use the defaults below and say where the file should go.

Two routes. Pick from my message, or ask which in one line:
- **Write it here:** an intent file in the repo. Use when there is no ticket yet, or the
  team keeps intents in the repo.
- **From a ticket:** I give a ticket key or link. The ticket stays the source of truth;
  no intent file is written.

## 1. Talk it through

Ask only product questions, in one batch, each with a suggested answer:
- What problem, for whom, and how do they get round it today?
- What changes for them when this is done?
- How will we know it works? Two to five checks a person could do.
- What is out of scope?
- Constraints: deadline, legal, brand, a customer commitment.

Never ask about files, data models, APIs, frameworks or effort. If the owner raises a
technical point, keep it as a constraint or an open question for engineering, in their
words. If they describe a solution, ask what it is for and record the need; keep the
solution only if they say it is required.

Read the code or existing projects only to avoid duplicating work already planned or shipped.
Don't put what you find there into the intent, beyond a one-line "Related:" pointer.

## 2a. Write it here

File: `active/` in the Intents folder from caddis.md (default `.caddis/intents/active/`),
named `intent-<kebab-name>.md`. It moves to `completed/` when a project delivers it. 15 to
40 lines:

```markdown
# <Title>

**Status:** Draft
**Owner:** <name>
**Ticket:** <key, or None>

## Problem
Who has it, what it costs them, how they cope today.

## Outcome
What is different for them when this is done.

## Done when
- A check a person can do, in product terms

## Out of scope
- ...

## Constraints
- ... (or omit)

## Open questions
- For product: ...
- For engineering: ...
```

Omit Constraints or Open questions when empty. Follow the Writing rules in caddis.md's
Product section. With none: short sentences, plain words, no jargon.

Show the owner the draft. When they accept it, set `**Status:** Accepted` and commit it as
its own `docs:` commit with the `commit` skill, unless `.caddis/` is gitignored. If you
can't commit directly (for example from claude.ai or Cowork), commit it with the GitHub
tool you have, or give the owner the file and its path.

## 2b. From a ticket

1. Read the ticket with the connected tracker tool (caddis.md's Tracker line names it). If
   none is connected, ask me to paste the ticket.
2. Check it against the sections in 2a. List what is missing or unclear, then ask about
   only those, as in step 1.
3. Draft the improved description using the 2a sections as headings. Show it, and update
   the ticket only when the owner says yes. Never overwrite their text silently. If the
   tracker can't be written to, give them the text to paste.

The ticket then is the intent. `/caddis:project <ticket key>` reads it directly.

## Output

Two lines: where the intent lives (file path or ticket key) and its status. Next step for
engineering: `/caddis:project <path or key>`.

## Rules

- Product terms only. If a section needs technical words, it belongs in the project.
- One intent per outcome. Split if the owner describes two.
- Never invent answers. An unanswered question stays under Open questions.

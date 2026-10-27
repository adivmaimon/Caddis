---
name: tests
description: Write and update tests for new or changed logic, following the frameworks, locations and priorities in caddis.md - highest-risk behaviour first, real assertions on outcomes, then run every suite.
---

Write and update tests for the change in hand, or for the area named in my message.

## Before writing

- Read the Tests section of `.caddis/caddis.md`: frameworks, where tests live per layer,
  the priorities in order, and the patterns to follow.
- Read two or three existing tests near the code to match their style, helpers and
  fixtures. Reuse helpers; don't build a parallel set.

## What to test, in order

1. The priorities caddis.md lists, top first. These are what must never break.
2. Anything enforcing an Invariant: one test per rule it enforces, including the failure
   path.
3. New and changed logic: the happy path, the edge cases, and malformed or missing input.
4. Bugs being fixed: a test that fails before the fix and passes after.

Skip what adds nothing: trivial getters, framework behaviour, styling.

## Patterns

- Assert outcomes the user or caller would notice, not internal state.
- Name the property under test, not the implementation: `rejects_a_wrong_checksum`, not
  `test_verify_2`.
- Small fixtures built in code with a known right answer.
- Planted-failure fixtures are first class: bad input, a dependency that times out, a
  response that is malformed. Each has a test that the code handles it.
- Mock the network, paid APIs and slow external services. Don't mock the code under test.
- Test data must not contain the exact strings the code searches for, unless that is the
  point of the test.
- Deterministic: fixed seeds, fixed clocks, no ordering assumptions.

## After writing

Run every suite with the Tests command in caddis.md. Report what was added and changed,
with pass counts. A failing pre-existing test is a decision, not a skip: work out whether
the test or the code is wrong, and fix that.

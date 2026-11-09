---
id: RCC-7
title: Implement documentation and comment rules
status: To Do
assignee: []
created_date: '2026-11-08 19:05'
updated_date: '2026-11-08 19:05'
labels: []
milestone: m-4
dependencies:
  - RCC-2
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the CC9xx family from doc-2: CC901 public API missing
docstring, CC902 commented-out code, CC903 TODO or FIXME without a
reference, and CC904 comments restating the following statement
(experimental). Only the checkable subset of the vendored clean-code
skill's `doc-*` position is encoded; docstring quality is explicitly
out of scope.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 CC901 exempts test files and private names as contracted, and never claims a present docstring is a good one.
- [ ] #2 CC902 never reports directives (`noqa`, `type:`, shebang, encoding), doctests, or prose; its parse attempt is conservative and its tests include prose comments that merely mention code.
- [ ] #3 CC903's reference pattern is configurable and its default is documented; the intentional overlap with Rude's example META001 is stated in user documentation.
- [ ] #4 CC904 ships last, at INFO, with its experimental status in the message documentation; it is removed rather than tuned endlessly if its measured false positives dominate.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Write failing tests starting from directive and prose counterexamples for CC902/CC904 and exemption cases for CC901.
2. Implement CC901 and CC903 (deterministic) before CC902 and CC904 (heuristic).
3. Measure CC904 on a real repository, record the outcome, and verify with `pixi run ci`.
<!-- SECTION:PLAN:END -->

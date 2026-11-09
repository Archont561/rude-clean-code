---
id: RCC-3
title: Implement in-file heuristic rules
status: To Do
assignee: []
created_date: '2026-11-08 19:05'
updated_date: '2026-11-08 19:05'
labels: []
milestone: m-2
dependencies:
  - RCC-2
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: medium
type: feature
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the in-file heuristic family from doc-2: CC401-CC402 unclear
naming, CC403 repeated magic literals, CC501 duplicate function bodies
within one file, and CC601 repeated type-switch dispatch. These rules
report indicators, not verdicts; their messages and severities must say
so (INFO, except CC403/CC501 at structural WARNING per doc-2).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each rule implements its doc-2 contract, including its documented exemptions (dunder names for CC401, short scopes for CC402, trivial literals for CC403, minimum size for CC501).
- [ ] #2 Each rule has package-local violating and clean unit tests, including at least one known false-positive shape per rule documented as accepted behaviour or proven silent.
- [ ] #3 False-positive behaviour is measured on at least one real repository (for example this one) and the observed rate is recorded in the task notes before any severity is reconsidered.
- [ ] #4 CC501's same-file limitation is stated in its message wording and documentation; it is never presented as cross-file duplication detection.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Write failing tests per rule, starting from the false-positive shapes (decorators, dunders, test files, trivial literals).
2. Implement rules against the shared traversal and registry from RCC-2; extend the vague-name list only through `configure()`, never by editing defaults per consumer.
3. Run the rules over a real repository, record the false-positive notes, and verify with `pixi run ci`.
<!-- SECTION:PLAN:END -->

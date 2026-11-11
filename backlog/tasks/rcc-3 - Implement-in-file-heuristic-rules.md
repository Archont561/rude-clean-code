---
id: RCC-3
title: Implement in-file heuristic rules
status: Done
assignee:
  - '@agent'
created_date: 2026-11-08 19:05
updated_date: '2026-11-11T16:42:00Z'
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
- [x] #1 Each rule implements its doc-2 contract, including its documented exemptions (dunder names for CC401, short scopes for CC402, trivial literals for CC403, minimum size for CC501).
- [x] #2 Each rule has package-local violating and clean unit tests, including at least one known false-positive shape per rule documented as accepted behaviour or proven silent.
- [x] #3 False-positive behaviour is measured on at least one real repository (for example this one) and the observed rate is recorded in the task notes before any severity is reconsidered.
- [x] #4 CC501's same-file limitation is stated in its message wording and documentation; it is never presented as cross-file duplication detection.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Write failing unit tests for CC401, CC402, CC403, CC501, and CC601 covering violations, clean cases, exemptions (dunders, short scopes, trivial literals 0/1/-1/"", `min_lines`=5, nested scopes), same-file wording on CC501, and documented/silent false-positive shapes.
2. Implement CC401-CC403 (rules/naming.py), CC501 (rules/dry.py), and CC601 (rules/heuristics.py), and register them in plugin.py.
3. Run the heuristic rules across real repositories (this repository and installed rude) to measure false-positive rates, record observed rates in RCC-3 notes, and confirm severities.
4. Update Strict profile docs, consumer rule docs, layout/architecture docs, discovery tests, and verify `pixi run --locked doit ci` and tox.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented CC401-CC403 (rules/naming.py), CC501 (rules/dry.py), and CC601 (rules/heuristics.py) and registered them in plugin.py (26 rules total). CC501 states its same-file limitation in both its rule diagnostic and docs/reference/rules.md.

Real-repository false-positive measurement (CC4, CC5, CC6):
1) This repository production code (16 Python files, 3,063 LOC across rude-clean-code/src, automation/dodo.py, scripts): CC401 = 0 (0.00/1000 LOC), CC402 = 0 (0.00/1000 LOC), CC403 = 50 (16.32/1000 LOC: doit task dictionary keys in dodo.py and repeated option keys in rule configure methods), CC501 = 0 (0.00/1000 LOC), CC601 = 2 (0.65/1000 LOC: AST node-type if/elif dispatchers in errors.py and naming.py).
2) This repository full tree including tests (31 files, 6,163 LOC): CC401 = 0, CC402 = 0, CC403 = 142 (23.04/1000 LOC from repeated test strings/fixtures), CC501 = 0, CC601 = 2 (0.32/1000 LOC).
3) Installed rude linter package (40 Python files, 11,369 LOC): CC401 = 0, CC402 = 0, CC403 = 88 (7.74/1000 LOC after exempting `cast(...)` stringified types; remaining hits are AST node-type/token/error literals), CC501 = 5 (0.44/1000 LOC: 5 genuine duplicate methods in whitespace.py and control_flow.py, 0 false positives), CC601 = 3 (0.26/1000 LOC: AST visitor if/elif dispatchers).

Severity conclusion: keep CC401, CC402, CC601 at INFO and CC403, CC501 at WARNING inside the Strict profile (not enabled in Basic dogfooding) because CC401/CC402/CC501 showed 0 false positives and CC403/CC601 match their doc-2 expectations.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed RCC-3 (CC401-CC403, CC501, CC601) with real-repo measurements, updated documentation, and verified CI + tox.
<!-- SECTION:FINAL_SUMMARY:END -->

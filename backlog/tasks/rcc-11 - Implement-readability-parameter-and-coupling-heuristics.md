---
id: RCC-11
title: Implement readability, parameter, and coupling heuristics
status: To Do
assignee: []
created_date: '2026-11-09T23:05:00Z'
updated_date: '2026-11-09T23:06:00Z'
labels: []
milestone: m-4
dependencies:
  - RCC-3
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the additional in-file readability, signature, and coupling
heuristics from doc-2: CC106 (unused function parameter), CC108 (data clumps
across signatures), CC307 (inverted if-not with else branch), CC604 (Law of
Demeter chained attribute/call access), and CC605 (external access to
single-underscore private members). These rules require careful exemptions
(guard clauses, abstract/protocol stubs, fluent chains, test files) and
must measure real-repo false-positive rates before any severity promotion.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All five rules ship at INFO severity with indicator wording and documented exemptions (guard clauses without else for CC307, protocol/override stubs and `self`/`cls`/`*args`/`**kwargs` for CC106, configurable `allowed_prefixes` and multiline tolerance for CC604, test files and `_asdict`/`_replace` for CC605).
- [ ] #2 Before and after implementation, expected false positives and measured hit rates on at least one real repository are recorded in task notes.
- [ ] #3 Each rule has package-local violating, clean, and counterexample tests verifying zero false positives on exempted idioms.
<!-- AC:END -->

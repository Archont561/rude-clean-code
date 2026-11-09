---
id: RCC-6
title: Implement maturing heuristic rules
status: To Do
assignee: []
created_date: '2026-11-08 19:05'
updated_date: '2026-11-08 19:05'
labels: []
milestone: m-4
dependencies:
  - RCC-3
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the indicator-grade rules deferred until their
false-positive behaviour could be judged: CC105 boolean flag
parameters, CC204 constructor dependency counts, CC205 responsibility
clusters, CC206 interface surface, CC304 complex expressions, CC305
unnecessary abstractions, CC503 repeated validation, CC504 repeated
constants (file-scope subset), CC602 suspicious overrides, and CC603
fat-interface indicators. All ship at INFO unless measurement on real
repositories justifies more (doc-2).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each rule's doc-2 contract is implemented with its severities and indicator wording; no message claims an SRP, LSP, or ISP violation as fact.
- [ ] #2 Before implementation, each rule's expected false positives are listed in the task notes; after implementation, its hit rate on at least one real repository is recorded there.
- [ ] #3 Rules whose visible base/interface is absent from the file stay silent (CC602, CC603, CC305); tests prove silence rather than guessing from names alone.
- [ ] #4 Any rule whose measured false-positive rate is unacceptable is dropped or kept INFO with the evidence recorded, not silently shipped at WARNING.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. For each rule, write the false-positive expectations and failing tests before the implementation; group rules that share analysis (CC205/CC206, CC602/CC603).
2. Implement against `ScopeProvider`/`QualifiedNameProvider` where doc-2 calls for semantic data, keeping per-file limits explicit.
3. Measure on a real repository, record results, adjust severity only on evidence, and verify with `pixi run ci`.
<!-- SECTION:PLAN:END -->

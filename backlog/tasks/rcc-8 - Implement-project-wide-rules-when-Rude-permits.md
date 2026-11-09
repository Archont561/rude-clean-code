---
id: RCC-8
title: Implement project-wide rules when Rude permits
status: To Do
assignee: []
created_date: '2026-11-08 19:05'
updated_date: '2026-11-08 19:05'
labels: []
milestone: m-5
dependencies:
  - RCC-2
documentation:
  - backlog/docs/doc-1 - Rude-Clean-Code-product-and-architecture-specification.md
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement CC203 (inheritance depth), CC502 (cross-file duplication),
and CC703 (circular dependencies) from doc-2. This task is blocked on
capability, not effort: Rude 0.1a4 gives rules a per-file context with
no project-level lifecycle hook, so these detections cannot be honest
`Rule`s yet. The codes stay reserved and unimplemented rather than
being faked with per-file approximations or process-global caches.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The task starts with a recorded assessment: either the installed Rude exposes a project-level provider or lifecycle hook sufficient for an order-independent, parallel-safe index, or a new backlog decision approves a separate indexer distribution (decision-1). Without one of these, the task stops and reports the blocker instead of shipping an approximation.
- [ ] #2 Detections are order-independent and give identical results under parallel checking (`--jobs` greater than 1) and single-process checking, proven by tests running the same fixture project both ways.
- [ ] #3 Each rule has fixture-project tests (multi-file packages with known cycles, duplications, and inheritance chains), including acyclic and non-duplicated projects reporting nothing.
- [ ] #4 Until this task lands, no release notes, README, or rule documentation claims CC203, CC502, or CC703 as available.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Re-check the installed Rude release for project-level providers; record the assessment in the task notes and, if needed, draft the indexer-distribution decision for user approval.
2. Build the project index (module graph, inheritance graph, normalised subtree hashes) behind whichever mechanism step 1 approved.
3. Implement the three rules on the index with multi-file fixtures, verify parallel and single-process equivalence, and run `pixi run ci`.
<!-- SECTION:PLAN:END -->

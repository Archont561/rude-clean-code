---
id: RCC-15
title: Assess a broader Feature Envy detector after CC606 ships
status: To Do
assignee: []
created_date: '2026-11-15T13:53:00Z'
updated_date: '2026-11-15T13:53:00Z'
labels: []
milestone: m-6
dependencies:
  - RCC-13
references:
  - https://github.com/Archont561/rude-clean-code/issues/27
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: spike
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CC606 as scoped covers one narrow, honest shape: two parameters of the same annotated type read for their attributes. Issue #27 points at the wider smell the clean-code skill names (`doc-*`, `.agents/skills/refactor`) in which a method uses another object's data more than its own, and that shape appears in this repository too: every rule visitor touches far more of the node it inspects than of `self`. The narrow rule deliberately does not attempt it.

The wider detector needs evidence before code exists. A per-file heuristic that fires on every visitor in this very plugin would be unusable, and a threshold tuned until this repository looks clean would be dishonest. The spike measures the shape on real code, decides whether a per-file proxy is trustworthy at all, and records the answer so a future task either implements it with a measured budget or declines it with a reason. No rule code ships from this task.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The assessment records, for at least five real repositories including this one, how often a method or function reads more foreign attributes than locals or `self` attributes, and what share of those hits are conventional idioms (visitors, serializers, comparators, adapters, test helpers).
- [ ] #2 The note states a recommendation with evidence: implement a per-file heuristic with named thresholds, or decline it as out of reach for a per-file analyzer, and either way names the rule code that would carry it (or why the code stays unallocated).
- [ ] #3 If the recommendation is to implement, a follow-up backlog task is created under m-6 with acceptance criteria in the same shape as RCC-13; if it is to decline, doc-2 records the decision next to the CC6xx family so the gap is documented rather than rediscovered.
- [ ] #4 `backlog/docs/doc-1 - Rude-Clean-Code-product-and-architecture-specification.md` and doc-2 describe the CC6xx family consistently after the assessment, with no rule claimed as shipped before it exists.
<!-- AC:END -->

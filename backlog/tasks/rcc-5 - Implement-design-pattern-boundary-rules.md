---
id: RCC-5
title: Implement design-pattern boundary rules
status: Done
assignee: []
created_date: 2026-11-08 19:05
updated_date: '2026-11-11T17:53:00Z'
labels: []
milestone: m-3
dependencies:
  - RCC-4
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: medium
type: feature
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the CC8xx family from doc-2: CC801 data access outside the
repository layer, CC802 products instantiated outside their factory,
CC803 strategy classes not implementing the strategy protocol, CC804
handlers missing their registration decorator, and CC805 concrete
construction bypassing dependency injection (INFO). These rules enforce
the boundaries of a pattern a consumer has adopted; no rule in this
family requires a pattern to exist, and none is added that does.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every CC8xx rule is inert when unconfigured (dedicated test, as in RCC-4) and reuses RCC-4's module/path matching machinery instead of duplicating it.
- [x] #2 Each rule has package-local violating and clean tests using a small, realistic consumer-shaped fixture (repository/strategy/factory/handler layouts), including the legitimate-location case (the repository importing the ORM, the factory constructing the product) reporting nothing.
- [x] #3 Documentation for each rule states the adopted-pattern precondition in its first paragraph, so a consumer without that pattern knows to leave it unconfigured.
- [x] #4 No rule is introduced that requires a pattern's presence; any "missing pattern" feedback remains with CC601/CC305/CC204 at INFO.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Build the consumer-shaped fixture packages first (layers, factories, strategies, handlers) and write failing tests against them.
2. Implement CC801-CC804 on RCC-4's machinery, then CC805 at INFO with composition-root path exclusions.
3. Document the opt-in precondition per rule and verify with `pixi run ci`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented CC801-CC804 (WARNING) and CC805 (INFO) reusing RCC-4's shared matching machinery, package-local consumer fixture tests, BDD coverage, and per-rule documentation stating adopted-pattern preconditions in the first paragraph.
<!-- SECTION:NOTES:END -->

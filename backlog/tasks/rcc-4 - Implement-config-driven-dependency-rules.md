---
id: RCC-4
title: Implement config-driven dependency rules
status: Done
assignee: []
created_date: 2026-11-08 19:05
updated_date: '2026-11-11T17:53:00Z'
labels: []
milestone: m-3
dependencies:
  - RCC-2
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: medium
type: feature
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement CC701 (forbidden concrete imports in domain code), CC702
(concrete instantiation in domain code), and CC704 (generalised
forbidden layer dependencies) from doc-2. These rules are inert until a
consumer names modules, classes, and paths; that inertness is a
contract, not a missing feature. This task also builds the shared
config-driven machinery (module reading from the first `dotted_name`
child, path scoping) that RCC-5's pattern rules reuse.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 With no `[tool.rude.rules.CC70x]` configuration, each rule reports nothing on any input, proven by a dedicated unit test per rule.
- [x] #2 Configured rules report exactly the documented matches, including `from x import y` forms, submodule matches, and `only_paths`/`exclude_paths` scoping against real file paths (not only `check_source`).
- [x] #3 CC704 is implemented as the general mechanism and CC701 remains the documented simple case; there is one shared module/path matching helper, not three copies.
- [x] #4 The Architecture profile snippet is published with placeholder module and path names that consumers must adapt, and says so.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Write failing tests for the unconfigured-inert contract first, then for configured matching on real files in a temporary tree.
2. Implement the shared matching helper and CC701 as the reference rule; add CC702 and CC704 on the same machinery.
3. Publish the Architecture profile snippet and verify with `pixi run ci`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented CC701, CC702, CC704 with shared module/path/call helpers (_architecture.py, _symbol_matching.py), inert-when-unconfigured tests, real consumer fixture tree tests, BDD scenarios, and published Architecture profile snippet with placeholder-adaptation guidance.
<!-- SECTION:NOTES:END -->

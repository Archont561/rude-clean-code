---
id: RCC-10
title: Implement fail-fast error handling and structural rules
status: Done
assignee:
  - '@agent'
created_date: '2026-11-09T23:05:00Z'
updated_date: '2026-11-11T16:42:00Z'
labels: []
milestone: m-2
dependencies:
  - RCC-2
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: medium
type: feature
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement fail-fast error handling and deterministic structural rules from
doc-2: CC107 (unused private module helper), CC207 (excessive direct base
classes, distinct from project-wide CC203), CC306 (nested ternary
expressions), CC308 (global statement usage), CC309 (broad exception
swallowed), CC310 (missing raise ... from chaining), and CC311 (oversized
try block). Rude 0.1a4 does not ship flake8-bugbear or Clean Code fail-fast
checks, leaving silent exception swallowing, unchained re-raises, global
state mutation, and mixin proliferation unchecked.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CC309, CC310, and CC311 implement broad exception swallowing, missing exception chaining via ScopeProvider CTX_IN_EXCEPT, and oversized try-block limits at WARNING with bare re-raise and contextlib.suppress exemptions tested.
- [x] #2 CC306 and CC308 flag nested ternary expressions and global statements at WARNING while excluding nested scopes and test files per config.
- [x] #3 CC107 reports unused module-private helpers via ScopeProvider while exempting dunders and configured decorators; CC207 reports excessive direct superclasses excluding Generic/Protocol without reusing reserved code CC203.
- [x] #4 Every rule has package-local violating, clean, and exemption tests passing under pixi run --locked test.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Write failing unit tests for CC107, CC207, CC306, CC308, CC309, CC310, and CC311 covering violations, clean cases, own-scope boundaries, test exemptions, bare raise, contextlib.suppress, Generic/Protocol exemptions, and `ignore_decorators`.
2. Implement CC107 (rules/functions.py), CC207 (rules/classes.py), and CC306/CC308-CC311 (rules/complexity.py), and register them in plugin.py.
3. Update plugin discovery / BDD specs and verify via pytest, mypy, ruff, and doit dogfood.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented CC107 (rules/functions.py), CC207 (rules/classes.py), CC306 & CC308 (rules/complexity.py), and CC309-CC311 (rules/errors.py), registered in plugin.py. Note: rude 0.1a4 ScopeProvider does not mark Binding.is_used for forward references from function bodies and returns None from `node_context` for `raise_statement`, so CC107 combines Binding.is_used with non-shadowed Scope.uses and CC310 pairs ScopeProvider CTX_IN_EXCEPT checks with scope-bounded `except_clause` parent walking. Verified 90/90 tests (96.77% coverage), ruff, mypy, and doit dogfood.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed RCC-10 (CC107, CC207, CC306, CC308-CC311) with unit tests covering violations, clean cases, and all documented exemptions.
<!-- SECTION:FINAL_SUMMARY:END -->

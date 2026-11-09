---
id: RCC-10
title: Implement fail-fast error handling and structural rules
status: To Do
assignee: []
created_date: '2026-11-09T23:05:00Z'
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
- [ ] #1 CC309, CC310, and CC311 implement broad exception swallowing, missing exception chaining via ScopeProvider CTX_IN_EXCEPT, and oversized try-block limits at WARNING with bare re-raise and contextlib.suppress exemptions tested.
- [ ] #2 CC306 and CC308 flag nested ternary expressions and global statements at WARNING while excluding nested scopes and test files per config.
- [ ] #3 CC107 reports unused module-private helpers via ScopeProvider while exempting dunders and configured decorators; CC207 reports excessive direct superclasses excluding Generic/Protocol without reusing reserved code CC203.
- [ ] #4 Every rule has package-local violating, clean, and exemption tests passing under pixi run --locked test.
<!-- AC:END -->

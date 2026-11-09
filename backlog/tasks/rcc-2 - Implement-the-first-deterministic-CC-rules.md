---
id: RCC-2
title: Implement the first deterministic CC rules
status: To Do
assignee: []
created_date: '2026-11-08 18:30'
updated_date: '2026-11-08 19:05'
labels: []
milestone: m-1
dependencies:
  - RCC-1
documentation:
  - backlog/docs/doc-1 - Rude-Clean-Code-product-and-architecture-specification.md
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: high
type: feature
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the deterministic core from doc-2 (CC101-CC104, CC201-CC202,
CC301-CC303) as Rude rules registered through the `rude.plugins` entry
point, following decision-5 (flat codes, explicit severities) and the
per-file scope limits in doc-1 section 5. This task deliberately relaxes
decision-4: the package stops being a version-only scaffold.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The `rude-clean-code` distribution depends on a pinned Rude (`rude>=0.1a4,<0.2` while pre-1.0), registers one `rude.plugins` entry point, and still exposes only `VERSION` from `rude_clean_code/__init__.py` (decision-2); `RULES` lives in a submodule the entry point names.
- [ ] #2 Each of CC101-CC104, CC201-CC202, CC301-CC303 implements its doc-2 detection contract, sets an explicit severity, and accepts its documented option through `configure()`; diagnostics state measured value, limit, and suggested action.
- [ ] #3 Each rule has a package-local unit test with violating and clean source, a Hypothesis property test where it is a pure threshold, and nested functions/classes are never attributed to their enclosing function (shared own-scope traversal, tested).
- [ ] #4 An integration test proves discovery through the installed entry point and that `select` by `CC`, by family prefix (`CC1`), and by exact code selects the intended rules, against the actually installed Rude version.
- [ ] #5 The "package has no other source files" BDD assertion from RCC-1 is relaxed deliberately in the same change, consumer-facing profile snippets (Basic) are published, and user-visible behaviour has a Gherkin scenario in the owning package.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Write failing package-local unit, property, and BDD tests for the plugin machinery (entry point, RULES, selection) and for CC101 as the reference rule.
2. Implement the shared own-scope traversal and CC101, then repeat per rule against its doc-2 contract; never copy threshold logic between rules.
3. Wire `configure()` options, publish the Basic profile snippet, and verify with `pixi run ci` (ruff, mypy, coverage, dogfood with this plugin's own rules on this repo).
<!-- SECTION:PLAN:END -->

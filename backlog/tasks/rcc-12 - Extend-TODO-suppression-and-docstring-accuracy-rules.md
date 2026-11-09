---
id: RCC-12
title: Extend TODO, suppression, and docstring accuracy rules
status: To Do
assignee: []
created_date: '2026-11-09T23:05:00Z'
updated_date: '2026-11-09T23:06:00Z'
labels: []
milestone: m-4
dependencies:
  - RCC-7
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend CC903 and add CC905-CC910 from doc-2: configurable `keywords`,
optional expiry dates, and optional `forbidden_markers` on CC903; CC905
(empty or description-less TODO), CC906 (blanket or unexplained suppression
comments), CC907 (empty or placeholder docstrings), CC908 (docstring
parameter drift), CC909 (docstring return or yield mismatch), and CC910
(dangling string literals in bodies). CC901 only checks presence, leaving
placeholder docstrings, stale `Args:` sections, empty `TODO` markers, and
unexplained `# noqa` suppressions undetected.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 CC903 supports configurable `keywords`, optional `expiry_pattern` with deterministic `reference_date` override, and opt-in `forbidden_markers`; CC905 rejects empty or description-less TODO comments.
- [ ] #2 CC906 flags blanket `# noqa` / `# type: ignore` comments and configured suppression prefixes lacking a `-- reason` explanation.
- [ ] #3 CC907 detects whitespace, punctuation-only, or TODO-placeholder docstrings; CC908 flags phantom documented parameters by default (with missing-parameter reporting opt-in); CC909 flags `Returns:` sections on generators or `None`-only functions at INFO; CC910 flags dangling body string literals while exempting attribute docstrings.
- [ ] #4 Each rule and exemption has package-local violating, clean, and counterexample tests.
<!-- AC:END -->

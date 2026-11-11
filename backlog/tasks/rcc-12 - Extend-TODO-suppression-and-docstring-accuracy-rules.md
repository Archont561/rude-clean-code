---
id: RCC-12
title: Extend TODO, suppression, and docstring accuracy rules
status: Done
assignee: []
created_date: '2026-11-09T23:05:00Z'
updated_date: '2026-11-11T18:43:00Z'
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
- [x] #1 CC903 supports configurable `keywords`, optional `expiry_pattern` with deterministic `reference_date` override, and opt-in `forbidden_markers`; CC905 rejects empty or description-less TODO comments.
- [x] #2 CC906 flags blanket `# noqa` / `# type: ignore` comments and configured suppression prefixes lacking a `-- reason` explanation.
- [x] #3 CC907 detects whitespace, punctuation-only, or TODO-placeholder docstrings; CC908 flags phantom documented parameters by default (with missing-parameter reporting opt-in); CC909 flags `Returns:` sections on generators or `None`-only functions at INFO; CC910 flags dangling body string literals while exempting attribute docstrings.
- [x] #4 Each rule and exemption has package-local violating, clean, and counterexample tests.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Pre-implementation Expected False Positives (RCC-12)

- **CC903 (extended keywords, expiry, forbidden markers):** `HACK`/`WORKAROUND` explanatory notes if consumers extend `keywords` without adding ticket references, or non-marker uppercase tokens inside explanatory comments.
- **CC905 (empty or description-less TODO):** Short placeholder tags such as `# TODO(owner)` where context was assumed self-evident from surrounding code.
- **CC906 (blanket or unexplained suppression):** Legacy `# noqa` / `# type: ignore` lines carried over from older toolchains before code-specific ignores or `-- <reason>` annotations were adopted.
- **CC907 (empty or placeholder docstring):** Stub docstrings temporarily written as `"""..."""` or `"""TODO."""` during scaffolding.
- **CC908 (docstring parameter drift):** Functions accepting `**kwargs` that intentionally document well-known forwarded keyword keys in `Args:`, or docstrings written with prose colons not forming an `Args:`/`Parameters`/`:param:` block.
- **CC909 (docstring return or yield mismatch):** Abstract interface stubs or protocol methods documenting `Returns:` while containing `...`/`pass` (must be exempt), or helper decorators wrapping generators.
- **CC910 (dangling string literal in body):** Multiline string expressions used intentionally as SQL/query notes or forgotten string constants not immediately following a PEP 258 attribute assignment.

### Measured Real-Repository Results (RCC-12)

Measured across the same five real codebases (303 files / 90,713 LOC):

- **CC905 (`WARNING`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 0; `tox` = 0; `_pytest` = 2 (empty `# XXX` markers).
- **CC906 (`WARNING`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 0; `tox` = 0; `_pytest` = 19 (blanket `# type: ignore` lines). Also explicitly unmasks bare `# noqa` for `CC906` under `Linter` without disturbing `# noqa` for other rules.
- **CC907 (`WARNING`):** 0 hits across all five corpora.
- **CC908 (`WARNING`):** After supporting typed splat parameters (`*names: str`, `**markup: bool`) and exempting `**kwargs` forwarders, hits totaled `this_repo_src` = 0; `rude` = 0; `packaging` = 0; `tox` = 0; `_pytest` = 3 real docstring mismatches.
- **CC909 (`INFO`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 2; `tox` = 6; `_pytest` = 2 (generator functions declaring `Returns:` while base methods annotated with non-`None` types stay exempt).
- **CC910 (`WARNING`):** 0 false positives across all five corpora (PEP 258 attribute docstrings inside `try`/`if` blocks in `__init__` stay exempt).
<!-- SECTION:NOTES:END -->

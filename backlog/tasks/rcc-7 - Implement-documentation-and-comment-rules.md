---
id: RCC-7
title: Implement documentation and comment rules
status: Done
assignee: []
created_date: 2026-11-08 19:05
updated_date: '2026-11-11T18:43:00Z'
labels: []
milestone: m-4
dependencies:
  - RCC-2
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the CC9xx family from doc-2: CC901 public API missing
docstring, CC902 commented-out code, CC903 TODO or FIXME without a
reference, and CC904 comments restating the following statement
(experimental). Only the checkable subset of the vendored clean-code
skill's `doc-*` position is encoded; docstring quality is explicitly
out of scope.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CC901 exempts test files and private names as contracted, and never claims a present docstring is a good one.
- [x] #2 CC902 never reports directives (`noqa`, `type:`, shebang, encoding), doctests, or prose; its parse attempt is conservative and its tests include prose comments that merely mention code.
- [x] #3 CC903's reference pattern is configurable and its default is documented; the intentional overlap with Rude's example META001 is stated in user documentation.
- [x] #4 CC904 ships last, at INFO, with its experimental status in the message documentation; it is removed rather than tuned endlessly if its measured false positives dominate.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Write failing tests starting from directive and prose counterexamples for CC902/CC904 and exemption cases for CC901.
2. Implement CC901 and CC903 (deterministic) before CC902 and CC904 (heuristic).
3. Measure CC904 on a real repository, record the outcome, and verify with `pixi run ci`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Pre-implementation Expected False Positives (RCC-7)

- **CC901 (public API missing docstring):** Tiny self-explanatory property getters, simple data-model classes, or internal module helpers left without a leading underscore inside application packages (test files and `_`-prefixed/dunder names exempt).
- **CC902 (commented-out code):** Short prose notes containing valid Python-looking tokens (for example `# status = ready`, `# see foo(bar)`, `# note: value`, section banners, doctests, `noqa`, `type:` directives). Conservative parser requires valid statements beyond bare names/attributes and minimum line block thresholds.
- **CC903 (TODO/FIXME without reference):** Exploratory design comments containing `TODO` without a linked tracker during early prototyping, or lowercase prose uses of `todo`/`fixme` that are not action markers.
- **CC904 (comment restating the code — experimental):** Explanatory step summaries or type-clarification comments that happen to share domain nouns/verbs with the next line (`# parse module configuration` above `config = parse_module(path)`), making token overlap prone to high false positives. Will be measured empirically on real repositories and removed if false positives dominate.

### Measured Real-Repository Results (RCC-7)

Measured across five real codebases totaling 303 files / 90,713 LOC (`this_repo_src` 32 files / 6,863 LOC, `rude` 40 files / 11,369 LOC, `packaging` 22 files / 12,715 LOC, `tox` 130 files / 20,036 LOC, `_pytest` 79 files / 39,730 LOC):

- **CC901 (`WARNING`):** `this_repo_src` = 0; `rude` = 228; `packaging` = 46; `tox` = 587; `_pytest` = 679. Test files and `_`-prefixed names remain exempt.
- **CC902 (`INFO`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 0; `tox` = 0; `_pytest` = 1 (`_pytest/_py/path.py:440`, genuine commented-out `assert` block). Zero prose or directive false positives across 90,713 LOC.
- **CC903 (`WARNING`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 8; `tox` = 0; `_pytest` = 43. Configurable `reference_pattern` and `META001` overlap match the specification.
- **CC904 (`INFO`, experimental):** After scoping to standalone single-line `#` comments (excluding `#:` Sphinx doc comments and multi-line comment blocks) and matching only the immediately following statement header, hits totaled 8 across 90,713 LOC (`this_repo_src` = 0; `rude` = 5; `packaging` = 0; `tox` = 1; `_pytest` = 2). All 8 were real single-line restatements (`# Load config` above `config = load_config(...)`), so `CC904` ships at `INFO` with explicit experimental messaging.
<!-- SECTION:NOTES:END -->

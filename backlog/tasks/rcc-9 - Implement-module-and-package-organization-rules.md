---
id: RCC-9
title: Implement module and package organization rules
status: To Do
assignee: []
created_date: '2026-11-09T23:05:00Z'
updated_date: '2026-11-09T23:06:00Z'
labels: []
milestone: m-2
dependencies:
  - RCC-2
documentation:
  - >-
    backlog/docs/doc-1 -
    Rude-Clean-Code-product-and-architecture-specification.md
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: medium
type: feature
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the CC0xx module and package organization rules from doc-2: CC001
(module too large with AST-derived split suggestion into `<name>/__init__.py`
and submodules), CC002 (`__init__.py` facade-only check with configurable
`allowed_names` for decision-2 `VERSION` checks in this repo), CC003
(non-empty `__init__.py` requiring `__all__`), CC004 (deep relative
imports), and CC005 (private symbols exported in `__all__`). Without
module-level boundaries, large modules become hard to split safely and
package entry points accumulate runtime logic instead of acting as clean
facades.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 CC001 measures module line count against configurable `max_lines` under `[tool.rude.rules.CC001]`, excludes tests and configured paths, emits no autofix, and tailors its split suggestion to top-level symbol clusters, single dominant definitions, or existing `__init__.py` files.
- [ ] #2 CC002 flags non-re-export definitions and runtime logic in `__init__.py` at INFO while permitting docstrings, imports, `__all__`, dunder metadata, `TYPE_CHECKING` blocks, optional PEP 562 `__getattr__`/`__dir__`, and configured `allowed_names` (verified against `src/rude_clean_code/__init__.py`).
- [ ] #3 CC003 flags non-empty `__init__.py` files missing `__all__` (and omitted public re-exports when configured) at WARNING while skipping empty marker initializers and test files by default.
- [ ] #4 CC004 and CC005 implement deep relative-import limits and private `__all__` export detection with package-local violating, clean, and false-positive unit and BDD tests.
<!-- AC:END -->

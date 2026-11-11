---
id: RCC-9
title: Implement module and package organization rules
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
- [x] #1 CC001 measures module line count against configurable `max_lines` under `[tool.rude.rules.CC001]`, excludes tests and configured paths, emits no autofix, and tailors its split suggestion to top-level symbol clusters, single dominant definitions, or existing `__init__.py` files.
- [x] #2 CC002 flags non-re-export definitions and runtime logic in `__init__.py` at INFO while permitting docstrings, imports, `__all__`, dunder metadata, `TYPE_CHECKING` blocks, optional PEP 562 `__getattr__`/`__dir__`, and configured `allowed_names` (verified against `src/rude_clean_code/__init__.py`).
- [x] #3 CC003 flags non-empty `__init__.py` files missing `__all__` (and omitted public re-exports when configured) at WARNING while skipping empty marker initializers and test files by default.
- [x] #4 CC004 and CC005 implement deep relative-import limits and private `__all__` export detection with package-local violating, clean, and false-positive unit and BDD tests.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add shared path/test/option/decorator helpers in _scope.py.
2. Write failing unit and BDD tests for CC001-CC005 (including module split suggestions, __init__.py facade/VERSION `allowed_names`/TYPE_CHECKING/PEP 562 checks, __all__ completeness, relative depth, and private exports).
3. Implement CC001-CC005 in rude_clean_code/rules/modules.py and register them in plugin.py.
4. Enable CC0 dogfooding rules (with `allowed_names` = ["VERSION"] and `exclude_paths`) and verify via pytest, mypy, ruff, and doit dogfood.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented CC001-CC005 in rules/modules.py and rules/_module_analysis.py with shared path/option helpers in _scope.py, registered MODULE_RULES in plugin.py, enabled CC0 dogfooding in rude-clean-code/pyproject.toml (`allowed_names` = ["VERSION"], CC001 `exclude_paths` = ["automation/dodo.py"]), and verified 73/73 tests (94.41% coverage), ruff, mypy, and doit dogfood.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed RCC-9 (CC001-CC005) with unit + BDD tests, dogfooding, and verified clean CI checks.
<!-- SECTION:FINAL_SUMMARY:END -->

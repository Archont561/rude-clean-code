---
id: RCC-11
title: Implement readability, parameter, and coupling heuristics
status: Done
assignee: []
created_date: '2026-11-09T23:05:00Z'
updated_date: '2026-11-11T18:43:00Z'
labels: []
milestone: m-4
dependencies:
  - RCC-3
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the additional in-file readability, signature, and coupling
heuristics from doc-2: CC106 (unused function parameter), CC108 (data clumps
across signatures), CC307 (inverted if-not with else branch), CC604 (Law of
Demeter chained attribute/call access), and CC605 (external access to
single-underscore private members). These rules require careful exemptions
(guard clauses, abstract/protocol stubs, fluent chains, test files) and
must measure real-repo false-positive rates before any severity promotion.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All five rules ship at INFO severity with indicator wording and documented exemptions (guard clauses without else for CC307, protocol/override stubs and `self`/`cls`/`*args`/`**kwargs` for CC106, configurable `allowed_prefixes` and multiline tolerance for CC604, test files and `_asdict`/`_replace` for CC605).
- [x] #2 Before and after implementation, expected false positives and measured hit rates on at least one real repository are recorded in task notes.
- [x] #3 Each rule has package-local violating, clean, and counterexample tests verifying zero false positives on exempted idioms.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Pre-implementation Expected False Positives (RCC-11)

- **CC106 (unused function parameter):** Framework/plugin hook callbacks (`pytest` hooks, `logging` formatters, `__exit__` `(exc_type, exc_val, exc_tb)`, signal handlers, subclass overrides of external base classes) that keep signature parameters for interface compatibility without leading underscores.
- **CC108 (data clump in signatures):** Cohesive CRUD/domain functions or handler methods inside one module that share common context triplets (such as `(node, options, context)` or `(user_id, tenant_id, locale)`) before a context object is warranted.
- **CC307 (inverted conditional with `else` branch):** Intentional defensive-first branches where the error or negative check (`if not valid: raise ... / fallback else: ...`) reads more clearly than nesting or flipping, and `is not None` checks where checking presence before fallback is positive logic.
- **CC604 (chained attribute or call access):** Module-qualified namespaces (`import.sub.pkg.Symbol`), `pathlib.Path` chains, fluent builder pipelines, and AST/DOM navigation chains (`node.parent.parent`) within a single statement.
- **CC605 (external access to private member):** Helper functions in the same module inspecting `_internal` fields on peer instances (`__eq__` / serializer helpers), descriptor/dataclass internals, and standard library namedtuple/private hooks.

### Measured Real-Repository Results (RCC-11)

Measured across five real codebases totaling 300 files / 89,616 LOC (`this_repo_src` 29 files / 5,766 LOC, `rude` 40 files / 11,369 LOC, `packaging` 22 files / 12,715 LOC, `tox` 130 files / 20,036 LOC, `_pytest` 79 files / 39,730 LOC):

- **CC106 (`INFO`):** `this_repo_src` = 0; `rude` = 17 (1.50/1k LOC, mostly base-class default hooks such as `should_check_file` and signal handlers); `packaging` = 0; `tox` = 37 (1.85/1k LOC); `_pytest` = 82 (2.06/1k LOC, `pprint` dispatch handlers). Confirms `INFO` is required.
- **CC108 (`INFO`):** `this_repo_src` = 2 (0.35/1k LOC, shared `(code, option_name, raw)` helpers in `_scope.py` and `_architecture.py`); `rude` = 8 (0.70/1k LOC); `packaging` = 6 (0.47/1k LOC); `tox` = 14 (0.70/1k LOC); `_pytest` = 14 (0.35/1k LOC, recursive `_format` handlers). Pytest fixture signatures in test files also repeat parameter names by design; keep `INFO`.
- **CC307 (`INFO`):** `this_repo_src` = 0; `rude` = 2 (0.18/1k LOC); `packaging` = 2 (0.16/1k LOC); `tox` = 3 (0.15/1k LOC); `_pytest` = 19 (0.48/1k LOC). Very low rate once guard clauses and `elif` chains are exempt -> keep `INFO`.
- **CC604 (`INFO`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 0; `tox` = 6 (0.30/1k LOC); `_pytest` = 5 (0.13/1k LOC). Multiline and `self.` exemptions hold noise very low -> keep `INFO`.
- **CC605 (`INFO`):** `this_repo_src` = 0; `rude` = 12 (1.06/1k LOC); `packaging` = 182 (14.31/1k LOC, peer `_key`/`_order_key` comparator helpers in `_ranges.py`); `tox` = 62 (3.09/1k LOC, `argparse` private action internals); `_pytest` = 306 (7.70/1k LOC, peer `_rawentry`/`_repr_style` inspection). High rate on peer-instance internals validates keeping `CC605` strictly `INFO`.
<!-- SECTION:NOTES:END -->

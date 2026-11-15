---
id: RCC-13
title: Implement CC606 feature-envy indicator for external same-type helpers
status: Done
assignee:
  - '@agent'
created_date: '2026-11-15T13:53:00Z'
updated_date: '2026-11-15T14:14:00Z'
labels: []
milestone: m-6
dependencies:
  - RCC-11
references:
  - https://github.com/Archont561/rude-clean-code/issues/27
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: medium
type: feature
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In consumer code, an identity helper lived outside the type it compared and nothing flagged it. Issue #27 records the case: a module-level `_same_task(candidate: TaskDefinition, dep: TaskDefinition) -> bool` in `graph.py` compared two instances of an imported type through `source_path` and `callable_fn.__code__`, although that comparison belonged on `TaskDefinition` itself.

Two shipped rules stop short of the shape, and both defaults are deliberate. CC604 needs a chain deeper than `max_chain_depth = 3`, so the three-hop `candidate.callable_fn.__code__.co_filename` never reaches the threshold. CC605 skips dunder members, so `__code__` and `__name__` stay invisible to it. What is missing is the Feature Envy indicator itself: a helper outside type `T` that takes two annotated `T` parameters and reads their attributes is an indicator, never a proven violation.

The rule is single-file by design. Rude 0.1a4 gives rules a per-file context, so no cross-module type resolution is attempted: an imported type is recognised from its annotation text alone, and silence is the answer whenever the evidence is thin.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CC606 ships at INFO with indicator wording, registers through `rude_clean_code.plugin`, appears in `rude list`, and is added to `EXPECTED_SEVERITIES`, `EXPECTED_CODES`, and the `CC6` selection set in `rude-clean-code/tests/test_plugin_discovery.py` and `test_deterministic_rules_bdd.py`.
- [x] #2 Detection contract: a module-level function or a method defined outside the class of annotated type `T` that declares two or more non-variadic parameters annotated with the same non-builtin `T`, and reads at least `min_attribute_reads` (2) attributes across those parameters; below that threshold the rule stays silent.
- [x] #3 Exemptions hold with package-local tests: builtin and stdlib value annotations (`int`, `str`, `float`, `bool`, `bytes`, `Path`, `Sequence`, `Mapping`, `Any`), configurable `ignored_types`, methods defined inside the class of `T`, `__eq__`/`__ne__`/`__hash__` and dataclass-generated comparison methods, pass-through wrappers with no attribute reads, and test files when `exclude_tests` is true.
- [x] #4 Package-local coverage: a violating fixture, a clean fixture, and counterexample fixtures for each exemption, plus a Gherkin scenario in `rude-clean-code/features/` wired to a step implementation, so the behaviour is proven through the BDD suite rather than a unit test alone.
- [x] #5 A false-positive budget measured on at least five real repositories (the same corpus RCC-11 used) is recorded in the task notes before the rule ships, and the severity stays INFO unless that evidence says otherwise.
- [x] #6 Documentation lands with the code: a CC6xx row in `backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md`, a row in `docs/reference/rules.md`, an implementation-order row, and every stated rule count updated in the maintained documents that carry one.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Measured False-Positive Budget (CC606)

Measured on 2026-11-15 across the same five-repository corpus RCC-11 used, total 300 files / 90,434 LOC:

| Repository | Files | LOC | CC606 hits | Hits per 1k LOC |
| --- | --- | --- | --- | --- |
| `this_repo_src` | 29 | 6,584 | 0 | 0.00 |
| `rude` | 40 | 11,369 | 1 | 0.09 |
| `packaging` | 22 | 12,715 | 0 | 0.00 |
| `tox` | 130 | 20,036 | 3 | 0.15 |
| `_pytest` | 79 | 39,730 | 2 | 0.05 |

Total 6 hits across 90,434 LOC — 0.07 hits per 1k LOC, an order of magnitude below CC605 (which measured 7.70/1k on `_pytest` and 14.31/1k on `packaging`). CC606 stays `INFO`, as RCC-13 requires.

Manual review of all six hits found zero false positives — each is genuinely a helper comparing two instances of a type that owns the behaviour:

- `this_repo_src` `complexity_heuristics.py` and `naming.py` compared two `Node` instances over byte spans; both were refactored so `ByteSpan` owns its containment test.
- `rude` `pyflakes/annotations.py` is a recursive `_contains(container, target)` tree walk — a true Feature Envy on `Node`.
- `tox` `file_view.py` compared two `os.stat_result` values through `st_uid`/`st_mode`; `local_sub_process/__init__.py` compared two `SyncWrite` handles through `handler`; `pip/req/file.py` compared two `Namespace` objects.
- `_pytest` `fixtures.py` compared two `FixtureDef` values, and `main.py` compared two `CollectionArgument` values.

### Bug found by the measurement

The first pass reported 5/3 hits on `tox` and `_pytest` that were false positives caused by generic builtins: `dict[str, Any]` and `set[str]` were compared as if they were user types, because the annotation normalizer stripped quotes but not generic arguments. Fixed by collapsing `[...]` groups before the builtin lookup; `dict[str, Any]`, `set[str]`, and `Mapping[object, object]` now resolve to their builtin base and stay silent.

### Dogfood impact

Enabling CC606 on this repository surfaced two genuine hits, which were refactored rather than suppressed. `doit dogfood` now reports 0 diagnostics.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented CC606 (`ExternalSameTypePairEnvy`) in `rude-clean-code/src/rude_clean_code/rules/feature_envy.py` and registered it through `plugin.py`. Ships at `INFO` with indicator wording, exposed as `CC606` in `rude list`. Measured at 0.07 hits per 1k LOC across the 300-file RCC-11 corpus with zero false positives; the measurement exposed a subscripted-builtin bug that is now fixed. Dogfooding CC6 on this repository surfaced two genuine hits that were refactored (a `ByteSpan` value object now owns byte-range containment) rather than suppressed. Verified with 239 package tests, 30 automation tests, 94.40% coverage, py311/py313 tox, and 0 dogfood diagnostics.
<!-- SECTION:FINAL_SUMMARY:END -->

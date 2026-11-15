---
id: RCC-13
title: Implement CC606 feature-envy indicator for external same-type helpers
status: To Do
assignee: []
created_date: '2026-11-15T13:53:00Z'
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
- [ ] #1 CC606 ships at INFO with indicator wording, registers through `rude_clean_code.plugin`, appears in `rude list`, and is added to `EXPECTED_SEVERITIES`, `EXPECTED_CODES`, and the `CC6` selection set in `rude-clean-code/tests/test_plugin_discovery.py` and `test_deterministic_rules_bdd.py`.
- [ ] #2 Detection contract: a module-level function or a method defined outside the class of annotated type `T` that declares two or more non-variadic parameters annotated with the same non-builtin `T`, and reads at least `min_attribute_reads` (2) attributes across those parameters; below that threshold the rule stays silent.
- [ ] #3 Exemptions hold with package-local tests: builtin and stdlib value annotations (`int`, `str`, `float`, `bool`, `bytes`, `Path`, `Sequence`, `Mapping`, `Any`), configurable `ignored_types`, methods defined inside the class of `T`, `__eq__`/`__ne__`/`__hash__` and dataclass-generated comparison methods, pass-through wrappers with no attribute reads, and test files when `exclude_tests` is true.
- [ ] #4 Package-local coverage: a violating fixture, a clean fixture, and counterexample fixtures for each exemption, plus a Gherkin scenario in `rude-clean-code/features/` wired to a step implementation, so the behaviour is proven through the BDD suite rather than a unit test alone.
- [ ] #5 A false-positive budget measured on at least five real repositories (the same corpus RCC-11 used) is recorded in the task notes before the rule ships, and the severity stays INFO unless that evidence says otherwise.
- [ ] #6 Documentation lands with the code: a CC6xx row in `backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md`, a row in `docs/reference/rules.md`, an implementation-order row, and every stated rule count updated in the maintained documents that carry one.
<!-- AC:END -->

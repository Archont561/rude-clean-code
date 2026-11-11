---
id: RCC-6
title: Implement maturing heuristic rules
status: Done
assignee: []
created_date: 2026-11-08 19:05
updated_date: '2026-11-11T18:43:00Z'
labels: []
milestone: m-4
dependencies:
  - RCC-3
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the indicator-grade rules deferred until their
false-positive behaviour could be judged: CC105 boolean flag
parameters, CC204 constructor dependency counts, CC205 responsibility
clusters, CC206 interface surface, CC304 complex expressions, CC305
unnecessary abstractions, CC503 repeated validation, CC504 repeated
constants (file-scope subset), CC602 suspicious overrides, and CC603
fat-interface indicators. All ship at INFO unless measurement on real
repositories justifies more (doc-2).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each rule's doc-2 contract is implemented with its severities and indicator wording; no message claims an SRP, LSP, or ISP violation as fact.
- [x] #2 Before implementation, each rule's expected false positives are listed in the task notes; after implementation, its hit rate on at least one real repository is recorded there.
- [x] #3 Rules whose visible base/interface is absent from the file stay silent (CC602, CC603, CC305); tests prove silence rather than guessing from names alone.
- [x] #4 Any rule whose measured false-positive rate is unacceptable is dropped or kept INFO with the evidence recorded, not silently shipped at WARNING.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. For each rule, write the false-positive expectations and failing tests before the implementation; group rules that share analysis (CC205/CC206, CC602/CC603).
2. Implement against `ScopeProvider`/`QualifiedNameProvider` where doc-2 calls for semantic data, keeping per-file limits explicit.
3. Measure on a real repository, record results, adjust severity only on evidence, and verify with `pixi run ci`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Pre-implementation Expected False Positives (RCC-6)

- **CC105 (boolean flag parameter):** Constructors storing configuration toggles on `self` (for example `verbose: bool = False`), option setters, and CLI callbacks where boolean flags map directly to CLI switches rather than two distinct code paths.
- **CC204 (excessive constructor dependencies):** Manual data-container classes whose `__init__` declares more than five typed scalar/model attributes (`str`, `int`, `Path`, etc.) rather than collaborating services; requires real-repo check to judge WARNING vs INFO.
- **CC205 (likely multiple responsibilities):** Utility container classes with helper methods touching distinct subsets of cached fields, or subclasses overriding template hooks whose state lives on a base class (`self.<base_attr>`).
- **CC206 (oversized interface surface):** Facade, parser, AST-visitor, or repository protocol classes that legitimately expose more than 10 cohesive public operations.
- **CC304 (unnecessarily complex expression):** Idiomatic generator expressions, filter predicates, nested literal data structures, or SQL/builder call chains written in a single readable statement.
- **CC305 (unnecessary abstraction):** Abstract base or `Protocol` classes whose second implementation lives in another module (`plugins/` or user extensions) when one reference implementation lives in the same module. (Must stay silent when zero in-file implementations exist.)
- **CC503 (repeated validation logic):** Parallel command handlers, property validators, or schema normalizers repeating similar defensive `is None` / `isinstance` type-narrowing guards for mypy/type safety.
- **CC504 (repeated constant definitions):** Distinct domain constants whose independent values happen to match (for example independent retry/timeout defaults both set to `30`, or distinct configuration keys with identical sentinel literals). Requires real-repo check to confirm WARNING vs INFO.
- **CC602 (suspicious overridden method):** Subclass specializations that intentionally replace an inherited base default or return `None` when overriding an abstract/sentinel placeholder whose annotation allows `None`, or where external base class behavior is unseen. (Must stay silent without an in-file base.)
- **CC603 (interface segregation indicator):** Adapter/mock/read-only implementations inheriting a concrete base class or protocol where unsupported operations intentionally raise `NotImplementedError`. (Must stay silent without an in-file base.)

### Measured Real-Repository Results (RCC-6)

Measured across five real codebases totaling 299 files / 89,217 LOC (`this_repo_src` 28 files / 5,367 LOC, `rude` 40 files / 11,369 LOC, `packaging` 22 files / 12,715 LOC, `tox` 130 files / 20,036 LOC, `_pytest` 79 files / 39,730 LOC; plus `stdlib_sample` 74 files / 38,591 LOC):

- **CC105 (`INFO`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 3 (0.24/1k LOC, all real flag params such as `validate: bool = True`); `tox` = 6 (0.30/1k LOC, real mode params such as `recursive` and `ignore_errors`); `_pytest` = 4 (0.10/1k LOC). Low hit rate, genuine flag semantics -> keep `INFO`.
- **CC204 (`INFO`, downgraded from doc-2 `WARNING` per AC #4):** `this_repo_src` = 0; `rude` = 0; `packaging` = 6 (0.47/1k LOC, all 6 are typed data-container constructors in `pylock.py`); `tox` = 6 (0.30/1k LOC, mostly value containers such as `Outcome` and `ExecuteRequest`); `_pytest` = 9 (0.23/1k LOC, mostly typed value objects such as `Mark` and `TestReport`). Because annotation presence alone classifies 76% (16/21) typed data-object constructors as high service coupling, kept `CC204` at `INFO` rather than `WARNING`.
- **CC205 (`INFO`):** `this_repo_src` = 0; `rude` = 1 (0.09/1k LOC, `FileContext`); `packaging` = 0; `tox` = 6 (0.30/1k LOC); `_pytest` = 7 (0.18/1k LOC). Low rate, genuine multi-cluster classes -> keep `INFO`.
- **CC206 (`INFO`):** `this_repo_src` = 0; `rude` = 5 (0.44/1k LOC); `packaging` = 2 (0.16/1k LOC); `tox` = 8 (0.40/1k LOC); `_pytest` = 21 (0.53/1k LOC). Accurately surfaces wide public surfaces with per-file disclaimer -> keep `INFO`.
- **CC304 (`INFO`):** `this_repo_src` = 0 (after excluding sign-only `-1` unary literals); `rude` = 4 (0.35/1k LOC); `packaging` = 8 (0.63/1k LOC); `tox` = 44 (2.20/1k LOC); `_pytest` = 18 (0.45/1k LOC). Complex expressions in parsers and formatters -> keep `INFO`.
- **CC305 (`INFO`):** `this_repo_src` = 0; `rude` = 0; `packaging` = 0; `tox` = 2 (0.10/1k LOC); `_pytest` = 0; `stdlib_sample` = 2 (0.05/1k LOC). Zero hits on pure-interface files -> keep `INFO`.
- **CC503 (`INFO`):** 0 hits across 89k LOC (high-precision threshold requires >= 2 normalized parameter guards across >= 3 functions).
- **CC504 (`WARNING`):** 0 false positives across 89k LOC on the narrow file-scope subset (`UPPER_CASE` distinct constants sharing non-trivial literals) -> keep `WARNING` per `doc-2`.
- **CC602 (`INFO`):** Initial measurement flagged 6 false positives on `_pytest/mark/structures.py` `...` overload stubs; after exempting stub overrides (`...`/`pass`/`abstractmethod`) and parsing `@overload` cleanly via AST decorator nodes, hits dropped to `0` on `this_repo_src`/`rude`/`packaging`/`tox`/`_pytest` and `1` genuine LSP issue in `stdlib_sample` (`_ProactorDuplexPipeTransport.write_eof`).
- **CC603 (`INFO`):** 0 false positives across 89k LOC (stays silent without visible in-file bases).
<!-- SECTION:NOTES:END -->

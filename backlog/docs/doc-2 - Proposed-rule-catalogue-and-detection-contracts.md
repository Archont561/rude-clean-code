---
id: doc-2
title: Proposed rule catalogue and detection contracts
type: specification
created_date: 2026-11-08 19:00
updated_date: '2026-11-09T23:06:00Z'
tags:
  - specification
  - rules
  - clean-code
---
## Status and purpose

**Proposed rules, not implemented rules.** This document specifies every
rule `rude-clean-code` intends to provide: what it detects, how it detects
it with Rude 0.1a4's per-file API, what it may be configured with, and how
much it may be trusted. The package is a version-only scaffold
(decision-4), so nothing here exists as code. Doc-1 states the product
direction; this document is the rule-level contract that backlog tasks
implement against, one rule per change, each with package-local tests.

Conventions that apply to every rule below:

- Codes are flat, family in the first digit (decision-5), so `CC`,
  `CC1`, and `CC101` all select through Rude's prefix matching.
- Severity is part of the contract (doc-1 section 4): deterministic and
  structural rules are `WARNING`, heuristic and semantic rules are
  `INFO`. No proposed rule defaults to `ERROR`.
- Scope is one of: **file** (decidable inside one file with Rude's
  `Rule.check`), **config** (file-scope but inert until the consumer
  names modules, paths, or base classes), or **project** (needs a
  cross-file index Rude 0.1a4 does not provide; deferred per doc-1
  section 5, never faked with process-global caches).
- Counts never descend into nested function, class, or lambda scopes
  when measuring an enclosing function or class. A nested definition is
  measured by its own rule invocation.
- Every diagnostic message states the measured value, the configured
  limit, and a suggested action. The long explanation lives in the rule
  docstring and in this document; Rude diagnostics carry no structured
  explanation fields.
- A rule ships an autofix only where the transformation is provably
  safe (doc-1 section 5). For every rule below the default is: no fix.

## CC0xx Modules and packages

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC001 | Module too large | Structural / WARNING | file | On `MODULE`, measure `len(ctx.lines)` against `max_lines`. On `<name>.py` over the limit, inspect top-level definitions and in-file reference clusters via `ScopeProvider` to suggest splitting into `<name>/__init__.py` (re-exporting the public API with `__all__`) and focused submodules; when one class or function dominates the file, point to `CC201` or `CC101` first; when the file is already `__init__.py`, suggest moving implementations into sibling submodules. Never emits an autofix (doc-1 section 5). | `max_lines` (400), `exclude_tests` (true), `exclude_paths` ([]) |
| CC002 | `__init__.py` contains non-re-export code | Heuristic / INFO | file | Active only when `ctx.path.name == "__init__.py"`. Allows module docstrings, comments, `__future__` and standard imports, `__all__` assignments (`=` and `+=`), dunder metadata (`__version__`, `__author__`), `if TYPE_CHECKING:` blocks, optional PEP 562 `__getattr__`/`__dir__`, and names listed in `allowed_names` (such as metadata `VERSION` under decision-2 when running dogfood checks on this repo). Flags top-level `def`, `class`, control flow, and runtime assignments or calls. | `allowed_names` ([]), `allow_lazy_getattr` (true), `exclude_tests` (true), `exclude_paths` ([]) |
| CC003 | Non-empty `__init__.py` missing `__all__` | Deterministic / WARNING | file | Active only when `ctx.path.name == "__init__.py"`. Flags non-empty `__init__.py` files that import or define public names without assigning `__all__`; when `require_reexports_in_all` is true, also flags public imported names omitted from `__all__` (complements Rude's `F822` and `F401`). Empty or comment-only marker initializers are exempt when `allow_empty` is true. | `allow_empty` (true), `require_reexports_in_all` (true), `exclude_tests` (true), `exclude_paths` ([]) |
| CC004 | Deep relative import | Structural / WARNING | file | `IMPORT_FROM_STATEMENT` whose leading relative-import dot count exceeds `max_relative_depth`, indicating tight cross-package coupling. | `max_relative_depth` (2) |
| CC005 | Private symbol exported in `__all__` | Deterministic / WARNING | file | String literal in a module-level `__all__` assignment naming an underscore-prefixed identifier (excluding `__dunder__` names). | none |

## CC1xx Functions

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC101 | Function too long | Deterministic / WARNING | file | `FUNCTION_DEFINITION` node; `end_line - line + 1` against the limit. Decorated functions measure the definition node, not the decorator lines, unless a consumer asks otherwise in a later revision. | `max_lines` (30) |
| CC102 | Too many parameters | Deterministic / WARNING | file | `FUNCTION_DEFINITION`; `parameter_count`, which includes `self`/`cls`. The inclusion is deliberate and documented, so method budgets are honest about call-site cost. | `max_parameters` (5) |
| CC103 | Too many return statements | Deterministic / WARNING | file | Count `return_statement` descendants in the function's own scope only. Guard-clause style raises false positives, which is why this is a warning with a generous default, not an error. | `max_returns` (5) |
| CC104 | Too many local variables | Deterministic / WARNING | file | Distinct assignment targets in the function's own scope. First implementation may count assignment targets; the `ScopeProvider`-based binding count is the preferred revision and must keep the same code and option. | `max_locals` (10) |
| CC105 | Boolean flag parameter | Heuristic / INFO | file | A parameter annotated `bool` (or defaulted to `True`/`False`) whose name is a mode word (`validate`, `dry_run`, `force`, `recursive`, and consumer additions) suggests the function does two things. Name-based, therefore informational only. | `flag_names` (built-in list, extendable) |
| CC106 | Unused function parameter | Heuristic / INFO | file | `ScopeProvider` bindings in function scope where `is_parameter` is true and `is_used` is false, excluding names matching `ignore_prefixes`, `self`/`cls`, `*args`/`**kwargs`, abstract or protocol stub methods (body is `pass`, `...`, or `raise NotImplementedError`), `@override` methods, and test files when `exclude_tests` is true. | `ignore_prefixes` (`["_"]`), `exclude_tests` (true) |
| CC107 | Unused private module helper | Structural / WARNING | file | Top-level `_`-prefixed function or class in `module_scope` (not `__dunder__`) with `Binding.is_used` false via `ScopeProvider`. Restricted to `_`-prefixed helpers because public dead code needs project scope (m-5). Exempts definitions carrying any decorator listed in `ignore_decorators`. | `ignore_decorators` ([]) |
| CC108 | Data clump in signatures | Heuristic / INFO | file | On `MODULE`, detect identical parameter-name groups of at least `min_params` shared across at least `min_functions` functions or methods in one file, suggesting a data class or parameter object. | `min_params` (3), `min_functions` (3) |

## CC2xx Classes

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC201 | Class too large | Structural / WARNING | file | `CLASS_DEFINITION` span in lines. A size proxy only; it starts the cohesion conversation that CC205 carries, it does not conclude it. | `max_lines` (200) |
| CC202 | Too many methods | Structural / WARNING | file | Direct methods of the class body, including decorated definitions whose wrapper is a `decorated_definition`. Dunder protocol methods still count toward size but are reported in the message count so consumers can judge. | `max_methods` (15) |
| CC203 | Excessive inheritance depth | Structural / WARNING | project | Requires the resolved inheritance graph. Deferred (doc-1 section 5). The per-file approximation (number of direct bases) is a different signal and must not reuse this code. | `max_depth` (3) |
| CC204 | Excessive constructor dependencies | Structural / WARNING | file | Dependencies requested by `__init__` (annotated parameters beyond a small allowance) as an SRP/coupling proxy. Distinguishes data parameters from service parameters only by annotation presence in the first revision. | `max_dependencies` (5) |
| CC205 | Likely multiple responsibilities | Heuristic / INFO | file | Method groups that touch disjoint attribute sets, or that only share `self`, indicate separate responsibilities. Reports the number of disconnected method/attribute clusters, never a pass/fail SRP verdict. | `max_clusters` (2), `min_methods` (5) |
| CC206 | Oversized interface surface | Heuristic / INFO | file | Public methods on a class or protocol beyond a threshold, as an ISP indicator. Whether consumers actually use the whole surface is project scope and out of reach per file. | `max_public_methods` (10) |
| CC207 | Excessive direct base classes | Structural / WARNING | file | `CLASS_DEFINITION` listing more direct superclasses than `max_bases` (excluding names in `ignore_bases` such as `Generic` and `Protocol`) as a per-file composition-over-mixins indicator. Distinct from CC203, which stays reserved for project-wide inheritance depth. | `max_bases` (3), `ignore_bases` (`["Generic", "Protocol"]`) |

## CC3xx KISS, readability, and fail-fast

`CC301`–`CC303` complement Rude's built-in `C901` (cyclomatic
complexity); they measure simpler, different shapes and must be
documented as running alongside it, not replacing it.

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC301 | Excessive nesting | Deterministic / WARNING | file | Deepest control-structure nesting (`if`/`for`/`while`/`try`/`with`/`match`) in the function's own scope. | `max_depth` (4) |
| CC302 | Excessive boolean operands | Deterministic / WARNING | file | Operands in the outermost `boolean_operator` chain of an expression; nested operators of the same chain are counted once, inner expressions are judged on their own. | `max_operands` (3) |
| CC303 | Excessive branching | Deterministic / WARNING | file | Decision points (`if`, `elif`, `for`, `while`, `and`/`or`, ternary, `match` cases) per function, own scope. Overlap with `C901` is intentional and documented; consumers select one. | `max_branches` (10) |
| CC304 | Unnecessarily complex expression | Heuristic / INFO | file | A single expression combining multiple operator kinds, calls, and comprehensions past a token/operator budget. Expression shapes are judgement calls, hence informational. | `max_operators` (8) |
| CC305 | Unnecessary abstraction | Heuristic / INFO | file | An abstract base or protocol with a single in-file implementation and no other in-file consumer, flagged as speculative generality (YAGNI). Cross-file implementations make this a lower bound, so it can only ever suggest. | `min_consumers` (2) |
| CC306 | Nested ternary expression | Deterministic / WARNING | file | `CONDITIONAL_EXPRESSION` containing a nested `CONDITIONAL_EXPRESSION` outside nested function or lambda scopes. | none |
| CC307 | Inverted conditional with `else` branch | Heuristic / INFO | file | `IF_STATEMENT` that has an `else_clause` and a negated top-level condition (`not ...` or `!=`). Guard clauses without an `else` branch are exempt. | none |
| CC308 | Global statement usage | Deterministic / WARNING | file | `GLOBAL_STATEMENT` mutating module-level state inside a function or method; test files are exempt when `exclude_tests` is true. | `exclude_tests` (true) |
| CC309 | Broad exception swallowed | Structural / WARNING | file | `EXCEPT_CLAUSE` catching `Exception`, `BaseException`, or bare `except` whose body only `pass`es, uses `...`, `continue`s, or returns a trivial constant (`None`, `False`, `[]`, `{}`) without raising or logging (complements Rude's `PAT006` and `PAT007`). Exempts `contextlib.suppress` and test files when `exclude_tests` is true. | `exclude_tests` (true) |
| CC310 | Missing exception chaining | Deterministic / WARNING | file | `RAISE_STATEMENT` raising a newly constructed or named exception inside an `except` handler (`ScopeProvider` context `CTX_IN_EXCEPT`) without `from <cause \| None>`. Bare re-raise (`raise`) is exempt. | none |
| CC311 | Oversized `try` block | Structural / WARNING | file | `TRY_STATEMENT` `try:` suite span exceeding `max_lines` (excluding `except`/`else`/`finally` clauses and nested definitions), violating fail-fast scoping of failure points. | `max_lines` (20) |

## CC4xx Naming

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC401 | Unclear function name | Heuristic / INFO | file | Single-letter names and a built-in vague list (`data`, `process`, `handle`, `do_work`, ...). Dunder names are exempt: they are a protocol vocabulary, not vagueness. Consumers may extend, not shrink, the list in the first revision. | `vague_names` (extendable) |
| CC402 | Unclear class or variable name | Heuristic / INFO | file | Same vague/single-letter policy applied to class names and module-level or annotated assignments. Loop variables and conventional short names in short scopes are the known false positive and must be excluded by scope-size allowance. | `vague_names`, `max_short_scope` (5 lines) |
| CC403 | Repeated magic literal | Structural / WARNING | file | The same non-trivial literal (string or number, excluding `0`, `1`, `-1`, `""`) appearing at least N times in one file should become a named constant. Trivial-literal exclusions are part of the contract, not an implementation detail. | `min_occurrences` (3) |

## CC5xx DRY

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC501 | Duplicate function bodies | Structural / WARNING | file | On the `MODULE` node, group functions by whitespace-normalised body text past a minimum size; report each duplicate after the first, naming the original and its line. Cross-file duplication is CC502. | `min_lines` (5) |
| CC502 | Duplicate code blocks | Structural / WARNING | project | Normalised subtree hashing across files. Deferred (doc-1 section 5). | `min_lines` (10) |
| CC503 | Repeated validation logic | Heuristic / INFO | file | Structurally similar guard sequences (same ordered checks against the same parameter) in multiple functions of one file suggest an unextracted validator. Similarity thresholds are tuned to under-report. | `min_functions` (3) |
| CC504 | Repeated constant definitions | Structural / WARNING | file | The same constant name assigned the same literal in multiple modules is project scope; the file-scope subset (same literal assigned to differently named module constants in one file) is reported under this code with the narrower wording in the message. Full detection deferred. | `min_occurrences` (3) |

## CC6xx SOLID heuristics

These rules detect **indicators**, never violations; a linter cannot
prove an SRP, LSP, ISP, or Law of Demeter breach from syntax. All are
`INFO`, all messages must use indicator language ("suggests", "consider"),
and all are candidates for suppression per class or call site with
`# noqa: CC6xx` plus a reason comment.

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC601 | Repeated type-switch dispatch | Heuristic / INFO | file | At least N `isinstance` calls in one function's own scope, or an `if`/`elif` chain discriminating on the same attribute, suggests missing polymorphism or strategy (see also CC803). | `min_isinstance` (3) |
| CC602 | Suspicious overridden method | Semantic / INFO | file | An override (same name as a base-class method visible in the file) that raises `NotImplementedError`, narrows a parameter by removing defaults the base provides, or discards the base return shape where visible. Only in-file bases are visible; absence of a visible base means silence. | none |
| CC603 | Interface segregation indicator | Heuristic / INFO | file | A class implementing a protocol/ABC visible in the file while leaving multiple of its methods raising `NotImplementedError` suggests the interface is too fat for this client (complements CC206). | `max_unimplemented` (2) |
| CC604 | Chained attribute or call access | Heuristic / INFO | file | Outermost `ATTRIBUTE` or `CALL` expression chain whose hop count exceeds `max_chain_depth`, as a Law of Demeter indicator. Exempts configurable prefixes (`allowed_prefixes`) and optional multiline fluent chains (`ignore_multiline`). | `max_chain_depth` (3), `allowed_prefixes` (`["self."]`), `ignore_multiline` (true) |
| CC605 | External access to private member | Heuristic / INFO | file | `ATTRIBUTE` reading or assigning a single-underscore `_name` attribute (not `__dunder__`) on a receiver other than `self`, `cls`, or `super()`. Exempts test files when `exclude_tests` is true and standard protocol names in `allowed_members`. | `exclude_tests` (true), `allowed_members` (`["_asdict", "_replace", "_make"]`) |

## CC7xx Dependencies and architecture

Config-driven by design: a generic plugin cannot know a consumer's
layering, so these rules are inert until the consumer names modules and
paths. The first revision of each must report nothing at all when
unconfigured; that behaviour is itself under test.

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC701 | Forbidden concrete imports in domain code | Deterministic / WARNING | config | Import nodes whose module matches a consumer-named forbidden module or submodule, restricted to consumer-named domain paths (`FileContext.is_in_path`). Reads the module from the first `dotted_name` child; `Node.import_module` is unreliable for `from x import y` in Rude 0.1a4 and must not be used. | `forbidden_modules` ([]), `only_paths` ([]) |
| CC702 | Concrete instantiation in domain code | Deterministic / WARNING | config | `CALL` nodes constructing consumer-named concrete classes inside consumer-named domain paths; composition roots are excluded by path, which the consumer owns. Suggests constructor injection instead. | `concrete_classes` ([]), `only_paths` ([]), `exclude_paths` ([]) |
| CC703 | Circular dependencies | Structural / WARNING | project | Module import cycle in the project graph. Deferred (doc-1 section 5). | none |
| CC704 | Forbidden layer dependency | Deterministic / WARNING | config | Generalises CC701: consumer-declared (from-layer, forbidden-module-prefix) pairs matched per file. CC701 stays as the documented simple case, not a special case in code. | `forbidden` ([]) |

## CC8xx Design-pattern boundaries

Pattern rules enforce the **boundaries a pattern creates once adopted**,
never the decision to adopt it (doc-1, and the YAGNI rule
`core-yagni-abstractions` in the vendored clean-code skill). Requiring a
pattern where none was chosen is a false-positive factory; forbidding
bypasses of a chosen pattern is a guarantee. All CC8xx rules are
therefore config-scope and inert until configured.

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC801 | Data access outside the repository layer | Deterministic / WARNING | config | Consumer-named database/ORM modules may only be imported under consumer-named repository paths; elsewhere the import is reported. The repository counterpart of CC701 for consumers who name layers positively. | `data_modules` ([]), `repository_paths` ([]) |
| CC802 | Product instantiated outside its factory | Deterministic / WARNING | config | Consumer-named product classes may only be constructed under factory paths or in `create_*` factory functions. | `product_classes` ([]), `factory_paths` ([]) |
| CC803 | Strategy class not implementing the strategy protocol | Deterministic / WARNING | config | Classes under consumer-named strategy paths must inherit a consumer-named strategy base/protocol (`inherits_from`) and define the required method. | `strategy_base` (none), `required_method` (none), `strategy_paths` ([]) |
| CC804 | Handler missing its registration decorator | Deterministic / WARNING | config | Functions under consumer-named handler paths must carry a consumer-named decorator (`decorator_names`). Mirrors the repository's own built-in CLI discovery convention. | `required_decorator` (none), `handler_paths` ([]) |
| CC805 | Concrete construction bypassing dependency injection | Heuristic / INFO | config | A consumer-named service class constructed inside another service (rather than received as a constructor parameter) suggests bypassed injection. Construction at composition roots is excluded by path. | `service_classes` ([]), `exclude_paths` ([]) |

Explicitly not proposed: rules requiring a factory, strategy, observer,
or facade to **exist**. Presence of a pattern is a design decision;
absence smells are covered at `INFO` level by CC601, CC305, and CC204.

## CC9xx Documentation and comments

The vendored clean-code skill ranks comments and documentation lowest
(`doc-*`): code should explain itself, comments explain *why*, and
public APIs are documented. These rules encode only the checkable
subset of that position.

| Code | Rule | Kind / severity | Scope | Detection contract | Options (default) |
| --- | --- | --- | --- | --- | --- |
| CC901 | Public API missing docstring | Deterministic / WARNING | file | A public module, class, or function definition (name not underscore-prefixed) whose body's first statement is not a string literal. Test files are exempt (`FileContext.is_test_file`); `__init__` follows its class. Whether the docstring is *good* is not checkable and is never claimed. | `check_modules` (true), `check_classes` (true) |
| CC902 | Commented-out code | Heuristic / INFO | file | A comment (or consecutive comment block) whose text parses as Python statements and is not a doctest, directive (`noqa`, `type:`, shebang, encoding), or prose. Parse attempts must be conservative: any doubt means silence. | `min_lines` (2) |
| CC903 | TODO or FIXME without a reference | Deterministic / WARNING | file | A `COMMENT` node containing any configured keyword (`TODO`, `FIXME`, `XXX`, extendable with `HACK`, `WORKAROUND`, `BUG`) without a configurable reference pattern (ticket id, issue URL, or owner). Optional `expiry_pattern` flags dated markers older than `reference_date` (default current UTC date), and opt-in `forbidden_markers` flags disallowed tags outside test files. Overlaps Rude's example `META001` by design, since consumers of this plugin should not need two packs for one policy. | `reference_pattern` (ticket or URL shape), `keywords` (`["TODO", "FIXME", "XXX"]`), `expiry_pattern` (none), `reference_date` (none), `forbidden_markers` ([]), `exclude_tests` (true) |
| CC904 | Comment restating the code | Heuristic / INFO | file | A comment whose normalised words are a near-subset of the identifiers in the immediately following statement (`# increment counter` above `counter += 1`). Experimental: token overlap is a weak signal, this rule ships last in its family and may be removed on false-positive evidence. | `max_overlap` (0.8) |
| CC905 | Empty or description-less TODO comment | Deterministic / WARNING | file | A `COMMENT` matching `keywords` that contains fewer than `min_description_chars` non-whitespace characters after removing the keyword and optional ticket reference (for example `# TODO:` or `# TODO(JIRA-123)`). | `keywords` (`["TODO", "FIXME", "XXX"]`), `min_description_chars` (3) |
| CC906 | Blanket or unexplained suppression comment | Structural / WARNING | file | A `COMMENT` containing `# noqa` or `# type: ignore` without explicit codes (mirrors Rude's `META002`/`META003` for plugin-only users), or suppressing any rule prefix listed in `require_reason_for` without a trailing `-- <reason>` explanation. | `require_reason_for` ([]) |
| CC907 | Empty or placeholder docstring | Deterministic / WARNING | file | A docstring on a public module, class, or function (via `Node.docstring()`, same scope and exemptions as CC901) whose stripped content is empty, punctuation-only (`...`), or starts with a `TODO`/`FIXME` placeholder. | `check_modules` (true), `check_classes` (true) |
| CC908 | Docstring parameter drift | Structural / WARNING | file | When a function or method docstring includes an explicit `Args:`, `Parameters`, or `:param <name>:` section, report documented parameter names absent from `node.parameters` (phantom parameters). When `report_missing` is true, also report undocumented non-`self`/`cls`/`*`/`**` parameters. | `report_missing` (false) |
| CC909 | Docstring return or yield mismatch | Heuristic / INFO | file | A function docstring declaring a `Returns:` section when the function's own scope contains `yield` or `yield from` (suggesting `Yields:`), or contains no value-returning `return` statement. | none |
| CC910 | Dangling string literal in body | Structural / WARNING | file | A module-, class-, or function-body `EXPRESSION_STATEMENT` holding a bare `STRING` that is neither the definition docstring nor an attribute docstring immediately following an assignment. | none |

## Implementation order

Backlog tasks implement rules in doc-1 section 6 order, tightened here.
Each row is one backlog task in one milestone; a task is not done while
any rule in its row lacks violating and clean tests.

| Order | Backlog task | Milestone | Rules |
| --- | --- | --- | --- |
| 1 | RCC-2 | m-1 | CC101–CC104, CC201–CC202, CC301–CC303 (deterministic core) |
| 2 | RCC-9 | m-2 | CC001–CC005 (module organization, `__init__.py` facade, and `__all__`) |
| 3 | RCC-10 | m-2 | CC107, CC207, CC306, CC308–CC311 (fail-fast error handling and deterministic structure extensions) |
| 4 | RCC-3 | m-2 | CC401–CC403, CC501, CC601 (in-file heuristics) |
| 5 | RCC-4 | m-3 | CC701, CC702, CC704 (config-driven dependency rules) |
| 6 | RCC-5 | m-3 | CC801–CC805 (design-pattern boundaries; after RCC-4's shared config machinery) |
| 7 | RCC-6 | m-4 | CC105, CC204–CC206, CC304–CC305, CC503–CC504, CC602–CC603 (maturing heuristics, false-positive budgets measured first) |
| 8 | RCC-11 | m-4 | CC106, CC108, CC307, CC604–CC605 (readability, signature, and coupling heuristics; false-positive budgets measured first) |
| 9 | RCC-7 | m-4 | CC901–CC904 (documentation and comments) |
| 10 | RCC-12 | m-4 | CC903 extensions, CC905–CC910 (extended TODO, suppression, and docstring accuracy rules) |
| 11 | RCC-8 | m-5 | CC203, CC502, CC703 (project scope; only when Rude exposes a project-level provider or a separate indexer distribution is decided, decision-1) |

# Rules and configuration profiles

`rude-clean-code` registers 26 Clean Code rules with Rude through the
`rude.plugins` entry point (`rude_clean_code.plugin`): 21 deterministic and
structural rules (`CC0xx`–`CC3xx`), 3 naming and literal heuristics
(`CC401`–`CC403`), 1 in-file duplication rule (`CC501`), and 1 in-file
polymorphism indicator (`CC601`). Remaining rule families (`CC502`,
`CC7xx`–`CC9xx`) in the
[rule catalogue](../../backlog/docs/doc-2%20-%20Proposed-rule-catalogue-and-detection-contracts.md)
remain planned.

## Configuration profiles

Rude 0.1a4 has no built-in preset flag, so copy either the **Basic** or
**Strict** profile snippet into your project's `pyproject.toml`.

### Basic profile (low-noise deterministic & structural checks)

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3"]

# Optional per-rule overrides (examples shown with their defaults):
[tool.rude.rules.CC101]
max_lines = 30

[tool.rude.rules.CC311]
max_lines = 15

[tool.rude.rules.CC107]
exclude_tests = true
```

### Strict profile (includes in-file heuristic indicators)

Add `"CC4"`, `"CC5"`, and `"CC6"` to enable naming/magic-literal checks,
same-file duplicate body detection, and repeated type-switch indicators:

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3", "CC4", "CC5", "CC6"]
```

You can also select the entire plugin with `select = ["CC"]` or run individual
rules from the command line:

```sh
rude check --select CC0,CC1,CC2,CC3 src/
```

All `CC0xx`–`CC3xx` rules (except `CC002` at `INFO`), plus `CC403` and
`CC501`, report `WARNING` severity, while `CC002` and subjective indicator
rules (`CC401`, `CC402`, `CC601`) report `INFO`.
Warnings and info diagnostics do not fail `rude check` with a non-zero exit
code. This repository itself dogfoods the **Basic** profile in
[`rude-clean-code/pyproject.toml`](../../rude-clean-code/pyproject.toml),
and `pixi run --locked doit dogfood` (enforced via `doit lint`, `pre-commit`,
and `ci`) inspects JSON diagnostics and fails on any warning or error across
`rude-clean-code`, `automation`, and `scripts`.

## Implemented rules

### Module organization (`CC0xx`)

| Code | Name | Severity | Option (default) | What it checks |
| --- | --- | --- | --- | --- |
| `CC001` | Module too large | `WARNING` | `max_lines = 400`, `exclude_tests = true`, `exclude_paths = []` | Total lines in a module with AST-derived split hints; test files are excluded by default. |
| `CC002` | `__init__.py` contains runtime logic | `INFO` | `allowed_names = []`, `allow_lazy_getattr = true`, `exclude_tests = true`, `exclude_paths = []` | Non-facade definitions, imports, or runtime statements in `__init__.py` (permits docstrings, imports, `__all__`, dunder metadata, `TYPE_CHECKING`, PEP 562 `__getattr__`/`__dir__`, and `allowed_names`). |
| `CC003` | `__init__.py` missing `__all__` | `WARNING` | `allow_empty = true`, `require_reexports_in_all = true`, `exclude_tests = true`, `exclude_paths = []` | Non-empty `__init__.py` files missing `__all__` or omitting public re-exports not listed in `__all__`. |
| `CC004` | Deep relative import | `WARNING` | `max_relative_depth = 2` | Relative `from ... import` statements whose leading dot count exceeds `max_relative_depth`. |
| `CC005` | Private symbol exported in `__all__` | `WARNING` | — | Single-underscore `_name` string literals placed inside module-level `__all__` assignments or augmented assignments. |

### Functions (`CC1xx`)

| Code | Name | Severity | Option (default) | What it measures |
| --- | --- | --- | --- | --- |
| `CC101` | Function too long | `WARNING` | `max_lines = 30` | Lines from `def` / `async def` to the end of the function body (decorators excluded). |
| `CC102` | Too many parameters | `WARNING` | `max_parameters = 5` | Parameter count in function signature (`self`/`cls`, `*args`, `**kwargs` included; `/` and `*` separators excluded). |
| `CC103` | Too many return statements | `WARNING` | `max_returns = 5` | `return` statements in the function's own scope only. |
| `CC104` | Too many local variables | `WARNING` | `max_locals = 10` | Distinct non-parameter, non-`global`, non-`nonlocal` bindings in the function's own scope via `ScopeProvider`. |
| `CC107` | Unused private helper | `WARNING` | `exclude_tests = true`, `ignore_decorators = []` | Module-level private helpers (`_name`, excluding dunders and `@overload`) that have no references anywhere in the module, including forward references. |

### Classes (`CC2xx`)

| Code | Name | Severity | Option (default) | What it measures |
| --- | --- | --- | --- | --- |
| `CC201` | Class too large | `WARNING` | `max_lines = 200` | Lines from `class` to the end of the class body (decorators excluded). |
| `CC202` | Too many methods | `WARNING` | `max_methods = 15` | Direct methods (including decorated methods) in the class body; dunder methods are counted and reported separately in the message. |
| `CC207` | Too many base classes | `WARNING` | `max_bases = 3`, `ignore_bases = ["Protocol", "ABC"]` | Direct base classes on a `class` header (excluding `metaclass=...` keywords and configured abstract/protocol markers). |

### Complexity and error handling (`CC3xx`)

| Code | Name | Severity | Option (default) | What it measures |
| --- | --- | --- | --- | --- |
| `CC301` | Excessive nesting | `WARNING` | `max_depth = 4` | Deepest `if`/`for`/`while`/`try`/`with`/`match` nesting in the function's own scope. |
| `CC302` | Excessive boolean operands | `WARNING` | `max_operands = 3` | Operands in the outermost `boolean_operator` chain of an expression; parenthesized inner chains are judged separately. |
| `CC303` | Excessive branching | `WARNING` | `max_branches = 10` | Own-scope decision points (`if`, `elif`, `for`, `while`, `and`/`or`, ternary `x if c else y`, and `match` `case` clauses). |
| `CC306` | Nested ternary | `WARNING` | — | A conditional expression (`x if cond else y`) nested inside another conditional expression (reported once per outer ternary). |
| `CC308` | Global statement | `WARNING` | `exclude_tests = true` | Any `global` statement, anywhere in non-test files. |
| `CC309` | Broad exception swallowed | `WARNING` | — | `except Exception` / `except BaseException` / bare `except:` whose handler has no `raise`, logging/warning call, or structured fallback value (`pass`/`...` or unconditional constant/literal return). |
| `CC310` | Missing exception chaining | `WARNING` | — | `raise SomeError(...)` inside an `except` handler (not in a nested function/class) without `from err` or `from None` (bare `raise` is exempt). |
| `CC311` | Oversized try block | `WARNING` | `max_lines = 15` | Line span of a `try` suite (excluding `except`, `else`, and `finally` clauses). |

### In-file heuristics (`CC4xx`, `CC5xx`, `CC6xx`)

Heuristic rules live in the **Strict** profile (`CC4`, `CC5`, `CC6`). They
surface maintainability indicators rather than hard defects:

| Code | Name | Severity | Option (default) | What it detects & limitations |
| --- | --- | --- | --- | --- |
| `CC401` | Unclear function name | `INFO` | `vague_names = [...]` | Function or method names built solely from vague words (`do`, `handle`, `process`, `data`, `info`, `helper`, `util`, `misc`, etc.) or single letters; dunders are exempt and `vague_names` extends the default list. |
| `CC402` | Unclear class or variable name | `INFO` | `vague_names = [...]`, `max_short_scope = 5` | Vague class names, module constants, or type-annotated locals in functions longer than `max_short_scope` lines (unannotated locals and short-function locals are exempt). |
| `CC403` | Repeated magic literal | `WARNING` | `min_occurrences = 3` | Numeric or non-empty string literals repeated in one file (exempts `0`, `1`, `-1`, `""`, docstrings, f-strings, `Literal[...]`/`Annotated[...]`/`cast(...)` types). Intentional test fixtures and DSL dictionary keys (e.g. `doit` task specs) are known false-positive shapes. |
| `CC501` | Duplicate function body | `WARNING` | `min_lines = 5` | Normalized function/method body lines (excluding comments, docstrings, whitespace, and `pass`/`...` stubs) duplicated inside the **same file**. Cross-file duplication is out of scope (`CC502` planned). |
| `CC601` | Repeated type switch | `INFO` | `min_isinstance = 3` | Functions with `>= N` own-scope `isinstance(...)` calls or `if`/`elif` chains comparing the same attribute across `>= N` branches (AST/dispatch visitors may trigger as benign indicators). |

## Own-scope isolation and Rude's `C901`

- Measurements for `CC103`, `CC104`, `CC202`, `CC301`, `CC303`, `CC310`, and
  `CC601` respect scope boundaries and do not leak nested functions, nested
  classes, or lambdas into an enclosing scope.
- `CC301`–`CC303` complement Rude's built-in `C901` (McCabe cyclomatic
  complexity) by measuring control depth, boolean chain length, and own-scope
  decision count without base-`1` or nested-function aggregation. When combining
  both (`select = ["E", "F", "C901", "CC0", "CC1", "CC2", "CC3"]`), consumers
  may ignore either `CC303` or `C901` depending on which branch metric they
  prefer.

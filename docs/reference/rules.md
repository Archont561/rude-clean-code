# Rules and configuration profiles

`rude-clean-code` registers 59 Clean Code rules with Rude through the
`rude.plugins` entry point (`rude_clean_code.plugin`): 21 deterministic and
structural rules (`CC001`–`CC005`, `CC101`–`CC104`, `CC107`, `CC201`–`CC202`,
`CC207`, `CC301`–`CC303`, `CC306`, `CC308`–`CC311`), 15 in-file heuristic and
indicator rules (`CC105`–`CC106`, `CC108`, `CC204`–`CC206`, `CC304`–`CC305`,
`CC307`, `CC401`–`CC403`, `CC501`, `CC503`–`CC504`, `CC601`–`CC605` — note
`CC403`, `CC501`, and `CC504` emit `WARNING`), 3 config-driven architecture
dependency rules (`CC701`, `CC702`, `CC704`), 5 config-driven design-pattern
boundary rules (`CC801`–`CC805`), and 10 documentation and comment hygiene
rules (`CC901`–`CC910`). Only the three project-wide rules (`CC203`, `CC502`,
`CC703`) in the
[rule catalogue](../../backlog/docs/doc-2%20-%20Proposed-rule-catalogue-and-detection-contracts.md)
remain planned.

## Configuration profiles

Rude 0.1a4 has no built-in preset flag, so copy the **Basic**, **Strict**,
**Architecture**, or **Documentation** profile snippet into your project's
`pyproject.toml`.

### Basic profile (low-noise deterministic & structural checks)

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3"]
# Exclude INFO-grade indicator heuristics inside CC1-CC3 (enabled in Strict):
ignore = [
  "CC105",
  "CC106",
  "CC108",
  "CC204",
  "CC205",
  "CC206",
  "CC304",
  "CC305",
  "CC307",
]

# Optional per-rule overrides (examples shown with their defaults):
[tool.rude.rules.CC101]
max_lines = 30

[tool.rude.rules.CC311]
max_lines = 15

[tool.rude.rules.CC107]
exclude_tests = true
```

### Strict profile (includes in-file heuristic indicators)

Remove the `ignore` list and add `"CC4"`, `"CC5"`, and `"CC6"` to enable
parameter, cohesion, expression, naming, magic-literal, duplication, SOLID,
and coupling indicators:

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3", "CC4", "CC5", "CC6"]
```

### Documentation and comments profile (`CC9`)

Add `"CC9"` to check public docstrings, stale docstring parameters, dangling
body string literals, commented-out code, unreferenced/expired `TODO` comments,
and blanket or unexplained suppressions:

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3", "CC9"]

[tool.rude.rules.CC903]
keywords = ["TODO", "FIXME", "XXX"]
reference_pattern = '(?:#\d+|[A-Z][A-Z0-9]+-\d+|https?://\S+|@[A-Za-z0-9_.-]+)'

[tool.rude.rules.CC906]
require_reason_for = ["CC6"]
```

### Architecture profile (opt-in dependency and pattern boundaries)

Add `"CC7"` and `"CC8"` to enable architecture and design-pattern boundary
checks. Every `CC7xx` and `CC8xx` rule is **inert until configured**, so
unconfigured rules emit zero diagnostics.

> **Important:** All module, class, decorator, and path names in this snippet
> (`domain/`, `sqlalchemy`, `SqlOrderRepo`, `repositories/`, `factories/`,
> `strategies/`, `handlers/`, `composition.py`, and so on) are **placeholders**
> that you **must adapt** to match your project's own layout and adopted
> patterns before copying them into `pyproject.toml`. Leave unconfigured any
> `CC8xx` rule whose pattern your project does not adopt.

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3", "CC4", "CC5", "CC6", "CC7", "CC8"]

# Simple single-layer forbidden imports (adapt placeholder names):
[tool.rude.rules.CC701]
forbidden_modules = ["sqlalchemy", "boto3", "myapp.infra"]
only_paths = ["src/myapp/domain/"]

# Direct concrete class construction inside domain code (adapt placeholders):
[tool.rude.rules.CC702]
concrete_classes = ["SqlOrderRepo"]
only_paths = ["src/myapp/domain/"]
exclude_paths = ["src/myapp/composition.py"]

# General multi-layer forbidden dependencies (adapt placeholders):
[[tool.rude.rules.CC704.forbidden]]
from_paths = ["src/myapp/domain/"]
forbidden_modules = ["sqlalchemy", "myapp.infra"]

# Optional pattern boundaries — configure ONLY the patterns you adopt:
[tool.rude.rules.CC801]
data_modules = ["sqlalchemy", "psycopg"]
repository_paths = ["src/myapp/repositories/"]

[tool.rude.rules.CC802]
product_classes = ["StripeGateway"]
factory_paths = ["src/myapp/factories/"]
exclude_paths = ["src/myapp/composition.py"]

[tool.rude.rules.CC803]
strategy_base = "PaymentStrategy"
required_method = "pay"
strategy_paths = ["src/myapp/strategies/"]

[tool.rude.rules.CC804]
required_decorator = "register_handler"
handler_paths = ["src/myapp/handlers/"]

[tool.rude.rules.CC805]
service_classes = ["EmailNotifier"]
exclude_paths = ["src/myapp/composition.py"]
```

You can also select the entire plugin with `select = ["CC"]` or run individual
rules from the command line:

```sh
rude check --select CC0,CC1,CC2,CC3 src/
```

Deterministic/structural rules, boundary rules (`CC7xx`, `CC801`–`CC804`),
`CC403`, `CC501`, `CC504`, `CC901`, `CC903`, `CC905`–`CC908`, and `CC910`
emit `WARNING` severity; `CC002`, `CC805`, `CC902`, `CC904` (experimental),
`CC909`, and all heuristic/indicator rules (`CC105`–`CC106`, `CC108`,
`CC204`–`CC206`, `CC304`–`CC305`, `CC307`, `CC401`–`CC402`, `CC503`,
`CC601`–`CC605`) emit `INFO`. Warnings and info diagnostics do not fail
`rude check` with a non-zero exit code. This repository itself dogfoods the
**Basic** profile in [`rude-clean-code/pyproject.toml`](../../rude-clean-code/pyproject.toml),
and `pixi run --locked doit dogfood` (enforced via `doit lint`, `pre-commit`,
and `ci`) inspects JSON diagnostics and fails on any warning or error across
`rude-clean-code` and `automation`.

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
| `CC105` | Boolean flag parameter | `INFO` | `flag_names = []` (extends built-ins) | Parameters annotated `bool` or defaulted to `True`/`False` whose names match mode-switch words (`dry_run`, `validate`, `force`, `recursive`, etc.); `flag_names` extends the default vocabulary. |
| `CC106` | Unused function parameter | `INFO` | `ignore_prefixes = ["_"]`, `exclude_tests = true` | Unused parameters via `ScopeProvider` (exempts `self`/`cls`, `*args`/`**kwargs`, `nonlocal` bindings, `pass`/`...`/`NotImplementedError` stubs, `@override`/`@abstractmethod`/`@overload`, and test files). |
| `CC107` | Unused private helper | `WARNING` | `exclude_tests = true`, `ignore_decorators = []` | Module-level private helpers (`_name`, excluding dunders and `@overload`) that have no references anywhere in the module, including forward references. |
| `CC108` | Data clump in signatures | `INFO` | `min_params = 3`, `min_functions = 3` | Maximal shared parameter groups of `>= min_params` non-variadic names recurring across `>= min_functions` signatures in one module. |

### Classes (`CC2xx`)

| Code | Name | Severity | Option (default) | What it measures |
| --- | --- | --- | --- | --- |
| `CC201` | Class too large | `WARNING` | `max_lines = 200` | Lines from `class` to the end of the class body (decorators excluded). |
| `CC202` | Too many methods | `WARNING` | `max_methods = 15` | Direct methods (including decorated methods) in the class body; dunder methods are counted and reported separately in the message. |
| `CC204` | Excessive constructor dependencies | `INFO` | `max_dependencies = 5` | Type-annotated `__init__` parameters beyond `max_dependencies` (empirical measurement showed 76% of real-world hits on typed data containers, so `CC204` ships as `INFO` rather than `WARNING`). |
| `CC205` | Likely multiple responsibilities | `INFO` | `max_clusters = 2`, `min_methods = 5` | Disconnected instance-method/`self` attribute clusters on classes with `>= min_methods` instance methods; emits indicator guidance, never claiming an SRP defect as fact. |
| `CC206` | Oversized interface surface | `INFO` | `max_public_methods = 10` | Non-private direct methods on a class or protocol exceeding `max_public_methods` (per-file ISP indicator only; call-site client usage is project scope). |
| `CC207` | Excessive direct base classes | `WARNING` | `max_bases = 3`, `ignore_bases = ["Generic", "Protocol"]` | Direct base classes on a `class` header (excluding `metaclass=...` keywords and configured abstract/protocol markers). |

### Complexity and error handling (`CC3xx`)

| Code | Name | Severity | Option (default) | What it measures |
| --- | --- | --- | --- | --- |
| `CC301` | Excessive nesting | `WARNING` | `max_depth = 4` | Deepest `if`/`for`/`while`/`try`/`with`/`match` nesting in the function's own scope. |
| `CC302` | Excessive boolean operands | `WARNING` | `max_operands = 3` | Operands in the outermost `boolean_operator` chain of an expression; parenthesized inner chains are judged separately. |
| `CC303` | Excessive branching | `WARNING` | `max_branches = 10` | Own-scope decision points (`if`, `elif`, `for`, `while`, `and`/`or`, ternary `x if c else y`, and `match` `case` clauses). |
| `CC304` | Unnecessarily complex expression | `INFO` | `max_operators = 8` | Expressions in statements exceeding `max_operators` operators/calls/comprehensions and spanning `>= 3` construct kinds (plain data literals and sign-only `-1` excluded). |
| `CC305` | Unnecessary abstraction | `INFO` | `min_consumers = 2` | `ABC`/`Protocol` classes visible in the same file with a single in-file subclass and fewer than `min_consumers` other references (stays silent when zero in-file subclasses exist). |
| `CC306` | Nested ternary | `WARNING` | — | A conditional expression (`x if cond else y`) nested inside another conditional expression (reported once per outer ternary). |
| `CC307` | Inverted conditional with `else` branch | `INFO` | — | Top-level `if not ...` or `if x != y` statements that include an `else:` branch (guard clauses without `else`, `elif` chains, and `is not None` checks are exempt). |
| `CC308` | Global statement | `WARNING` | `exclude_tests = true` | Any `global` statement, anywhere in non-test files. |
| `CC309` | Broad exception swallowed | `WARNING` | `exclude_tests = true` | `except Exception` / `except BaseException` / bare `except:` whose handler has no `raise`, logging/warning call, or structured fallback value (`pass`/`...` or unconditional constant/literal return). |
| `CC310` | Missing exception chaining | `WARNING` | — | `raise SomeError(...)` inside an `except` handler (not in a nested function/class) without `from err` or `from None` (bare `raise` is exempt). |
| `CC311` | Oversized try block | `WARNING` | `max_lines = 20` | Line span of a `try` suite (excluding `except`, `else`, and `finally` clauses, and excluding nested definitions). |

### Naming, magic literals, DRY, and SOLID heuristics (`CC4xx`–`CC6xx`)

Heuristic rules live in the **Strict** profile (`CC4`, `CC5`, `CC6`, plus the
`INFO` indicators in `CC1`–`CC3`). Rules whose base/interface lives outside
the file (`CC305`, `CC602`, `CC603`) stay silent rather than guessing from names:

| Code | Name | Severity | Option (default) | What it detects & limitations |
| --- | --- | --- | --- | --- |
| `CC401` | Unclear function name | `INFO` | `vague_names = [...]` | Function or method names built solely from vague words (`do`, `handle`, `process`, `data`, `info`, `helper`, `util`, `misc`, etc.) or single letters; dunders are exempt and `vague_names` extends the default list. |
| `CC402` | Unclear class or variable name | `INFO` | `vague_names = [...]`, `max_short_scope = 5` | Vague class names, module constants, or type-annotated locals in functions longer than `max_short_scope` lines (unannotated locals and short-function locals are exempt). |
| `CC403` | Repeated magic literal | `WARNING` | `min_occurrences = 3` | Numeric or non-empty string literals repeated in one file (exempts `0`, `1`, `-1`, `""`, docstrings, f-strings, `Literal[...]`/`Annotated[...]`/`cast(...)` types). Intentional test fixtures and DSL dictionary keys (e.g. `doit` task specs) are known false-positive shapes. |
| `CC501` | Duplicate function body | `WARNING` | `min_lines = 5` | Normalized function/method body lines (excluding comments, docstrings, whitespace, and `pass`/`...` stubs) duplicated inside the **same file**. Cross-file duplication is out of scope (`CC502` planned). |
| `CC503` | Repeated validation logic | `INFO` | `min_functions = 3` | Parameter-normalized leading guard-clause sequences (`if ...: raise/return`, at least two guards or a compound boolean guard) shared across `>= min_functions` functions in one file. |
| `CC504` | Repeated constant definitions | `WARNING` | `min_occurrences = 3` | File-scope subset: distinct module-level `UPPER_CASE` constants assigned the same non-trivial literal inside one file (cross-module constant duplication remains deferred). |
| `CC601` | Repeated type switch | `INFO` | `min_isinstance = 3` | Functions with `>= N` own-scope `isinstance(...)` calls or `if`/`elif` chains comparing the same attribute across `>= N` branches (AST/dispatch visitors may trigger as benign indicators). |
| `CC602` | Suspicious overridden method | `INFO` | — | Subclass overrides of visible in-file concrete base methods that raise `NotImplementedError`, strip base defaults, or return `None` where the base returns a value (silent when the base is external). |
| `CC603` | Interface segregation indicator | `INFO` | `max_unimplemented = 2` | Subclasses leaving `> max_unimplemented` methods inherited from a visible in-file base raising `NotImplementedError` (silent when the base is external). |
| `CC604` | Chained attribute or call access | `INFO` | `max_chain_depth = 3`, `allowed_prefixes = ["self."]`, `ignore_multiline = true` | Single-line `attribute`/`call` expression chains exceeding `max_chain_depth` hops outside `allowed_prefixes` (Law of Demeter indicator). |
| `CC605` | External access to private member | `INFO` | `exclude_tests = true`, `allowed_members = ["_asdict", "_replace", "_make"]` | Reading or writing single-underscore `_name` attributes on receivers other than `self`, `cls`, or `super()`. |

### Architecture and dependencies (`CC7xx`, opt-in config)

All `CC7xx` rules are **config-scoped and inert until configured** with your
project's module prefixes, class names, and path boundaries. (`CC703` cyclic
package dependencies remains planned for project scope.) `CC704` implements the
general layer-dependency engine, and `CC701` is the documented simple case for
one layer.

| Code | Name | Severity | Option (default) | What it enforces |
| --- | --- | --- | --- | --- |
| `CC701` | Forbidden concrete imports | `WARNING` | `forbidden_modules = []`, `only_paths = []`, `exclude_paths = []` | Simple single-layer wrapper over `CC704`: flags `import` and `from ... import` statements matching `forbidden_modules` (exact or submodule matches, including `from x import y`) inside `only_paths` (all non-excluded files when `only_paths` is empty). |
| `CC702` | Concrete instantiation in domain code | `WARNING` | `concrete_classes = []`, `only_paths = []`, `exclude_paths = []` | Flags direct call instantiations of configured `concrete_classes` inside `only_paths` while skipping `exclude_paths` (such as composition roots). Suggests injecting abstractions instead. |
| `CC704` | Forbidden layer dependency | `WARNING` | `forbidden = []` | General multi-layer dependency check accepting `[[from_paths, forbidden_modules]]` pairs or `{from_paths, forbidden_modules, exclude_paths}` mappings (`[[tool.rude.rules.CC704.forbidden]]`). |

### Design-pattern boundaries (`CC8xx`, opt-in config)

Every `CC8xx` rule is **inert until configured**. No `CC8xx` rule requires a
project to adopt any design pattern — pattern-absence indicators live in
`CC601`, `CC204`, and `CC305` at `INFO`.

#### `CC801`: Data access outside the repository layer

Precondition: configure `CC801` only if your project adopts the **Repository**
pattern to isolate persistence behind repository classes or modules; otherwise
leave `CC801` unconfigured so it stays inert.

- **Severity:** `WARNING`
- **Options:** `data_modules = []`, `repository_paths = []`,
  `exclude_paths = []`
- **Behavior:** Requires both `data_modules` and `repository_paths`. Imports
  matching `data_modules` (including `from x import y` and submodules) are
  permitted in files matching `repository_paths` or `exclude_paths` and
  flagged elsewhere.

#### `CC802`: Product instantiated outside its factory

Precondition: configure `CC802` only if your project adopts **Factory**
encapsulation (`factories/` modules or `create_*` factory functions) for
constructing specific product classes; otherwise leave `CC802` unconfigured.

- **Severity:** `WARNING`
- **Options:** `product_classes = []`, `factory_paths = []`,
  `only_paths = []`, `exclude_paths = []`
- **Behavior:** Flags direct instantiation calls for configured
  `product_classes` unless the file matches `factory_paths` / `exclude_paths`
  or the call sits inside an enclosing `create_*` function or method.

#### `CC803`: Strategy class violating the strategy protocol

Precondition: configure `CC803` only if your project organizes concrete
implementations of a **Strategy** pattern under dedicated strategy paths with
a shared base/protocol or required method; otherwise leave `CC803`
unconfigured.

- **Severity:** `WARNING`
- **Options:** `strategy_base = none`, `required_method = none`,
  `strategy_paths = []`, `exclude_paths = []`
- **Behavior:** Requires `strategy_paths` plus at least one of
  `strategy_base` or `required_method`. Module-level classes inside
  `strategy_paths` (excluding the `strategy_base` class itself and
  `exclude_paths`) must inherit `strategy_base` and define `required_method`.

#### `CC804`: Handler missing its registration decorator

Precondition: configure `CC804` only if your project uses
decorator-registered **handlers** (for example CLI commands, HTTP routes, or
event/message handlers) under dedicated handler paths; otherwise leave
`CC804` unconfigured.

- **Severity:** `WARNING`
- **Options:** `required_decorator = none`, `handler_paths = []`,
  `exclude_paths = []`, `ignore_private = true`
- **Behavior:** Requires both `required_decorator` (exact name or `fnmatch`
  pattern such as `"router.*"`, string or list) and `handler_paths`. Flags
  public top-level functions in `handler_paths` that omit the registration
  decorator, while sparing nested helpers, class methods, and private
  `_helper` functions when `ignore_private = true`.

#### `CC805`: Concrete service construction bypassing dependency injection

Precondition: configure `CC805` only if your project uses **dependency
injection** to supply collaborating services via constructor parameters and
restricts direct service instantiation to composition roots; otherwise leave
`CC805` unconfigured.

- **Severity:** `INFO`
- **Options:** `service_classes = []`, `only_paths = []`, `exclude_paths = []`
- **Behavior:** Emits an `INFO` indicator when a configured service class is
  instantiated outside `exclude_paths` (excluding self-construction inside the
  service class itself), suggesting constructor injection and wiring at a
  composition root.

### Documentation and comment hygiene (`CC9xx`)

| Code | Name | Severity | Option (default) | What it checks |
| --- | --- | --- | --- | --- |
| `CC901` | Public API missing docstring | `WARNING` | `check_modules = true`, `check_classes = true` | Public modules, classes, and functions/methods missing a leading docstring (exempts `_`-prefixed definitions, `@overload`, `@x.setter`/`deleter`, and test files; never judges docstring quality). |
| `CC902` | Commented-out code | `INFO` | `min_lines = 2` | Consecutive comment blocks conservatively parsing as valid Python statements; never flags shebangs, encodings, `noqa`/`type:` directives, doctests, banners, or prose. |
| `CC903` | TODO or FIXME without a reference | `WARNING` | `reference_pattern` (ticket `#123`, `JIRA-1`, URL, or `@owner`), `keywords = ["TODO", "FIXME", "XXX"]`, `expiry_pattern = none`, `reference_date = none`, `forbidden_markers = []`, `exclude_tests = true` | Marker comments missing a reference, dated tags past `reference_date` (or UTC today), or forbidden marker tokens outside test files. Intentionally overlaps Rude's example `META001` so plugin users need one rule pack. |
| `CC904` | Comment restating the code *(experimental)* | `INFO` | `max_overlap = 0.8` | Standalone single-line comments whose normalized words overlap at least `max_overlap` of identifiers on the immediately following statement line (rationale comments containing `why`/`because`/etc. are exempt). |
| `CC905` | Empty or description-less TODO | `WARNING` | `keywords = ["TODO", "FIXME", "XXX"]`, `min_description_chars = 3` | Marker comments lacking descriptive text once keyword, bracketed owner/tag, and ticket references are stripped. |
| `CC906` | Blanket or unexplained suppression comment | `WARNING` | `require_reason_for = []` | Blanket `# noqa` or `# type: ignore` without explicit codes (mirrors Rude `META002`/`META003`), plus targeted suppressions matching `require_reason_for` prefixes without a trailing `-- <reason>`. |
| `CC907` | Empty or placeholder docstring | `WARNING` | `check_modules = true`, `check_classes = true` | Public API docstrings whose stripped text is blank, punctuation-only (`...`), or starts with a `TODO`/`FIXME` placeholder. |
| `CC908` | Docstring parameter drift | `WARNING` | `report_missing = false` | Phantom parameter names in Google `Args:`, NumPy `Parameters`, or Sphinx `:param:` sections absent from the function signature (exempts `**kwargs` forwarders); set `report_missing = true` to also flag undocumented non-variadic signature parameters. |
| `CC909` | Docstring return or yield mismatch | `INFO` | — | Function docstrings declaring `Returns:`/`:returns:` on a generator function (suggests `Yields:`) or a `None`-only function outside stubs/non-`None` annotated interfaces. |
| `CC910` | Dangling string literal in body | `WARNING` | — | Standalone body string literal statements that are neither definition docstrings nor PEP 258 attribute docstrings following an assignment. |

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

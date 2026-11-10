# Rules and configuration profiles

`rude-clean-code` registers Clean Code rules with Rude through the
`rude.plugins` entry point (`rude_clean_code.plugin`). Only deterministic
core rules (`CC101`–`CC104`, `CC201`–`CC202`, and `CC301`–`CC303`) are
implemented today; heuristic, organization, dependency, and documentation
rules in the [backlog specification](../../backlog/docs/doc-2%20-%20Proposed-rule-catalogue-and-detection-contracts.md)
remain planned.

## Basic profile

Rude 0.1a4 has no built-in preset flag, so copy the **Basic** profile snippet
into your project's `pyproject.toml`:

```toml
[tool.rude]
select = ["CC1", "CC2", "CC3"]

# Optional per-rule threshold overrides (shown with their defaults):
[tool.rude.rules.CC101]
max_lines = 30

[tool.rude.rules.CC102]
max_parameters = 5

[tool.rude.rules.CC103]
max_returns = 5

[tool.rude.rules.CC104]
max_locals = 10

[tool.rude.rules.CC201]
max_lines = 200

[tool.rude.rules.CC202]
max_methods = 15

[tool.rude.rules.CC301]
max_depth = 4

[tool.rude.rules.CC302]
max_operands = 3

[tool.rude.rules.CC303]
max_branches = 10
```

You can also select the entire plugin with `select = ["CC"]` or run individual
rules from the command line:

```sh
rude check --select CC src/
```

All implemented `CC` rules report `WARNING` severity, so warnings remain
advisory and do not fail `rude check` with a non-zero exit code. This
repository itself dogfoods the **Basic** profile in
[`rude-clean-code/pyproject.toml`](../../rude-clean-code/pyproject.toml),
and `pixi run --locked doit dogfood` (enforced via `doit lint`, `pre-commit`,
and `ci`) inspects JSON diagnostics and fails on any warning or error across
`rude-clean-code`, `automation`, and `scripts`.

## Implemented rules

| Code | Name | Severity | Option (default) | What it measures |
| --- | --- | --- | --- | --- |
| `CC101` | Function too long | `WARNING` | `max_lines = 30` | Lines from `def` / `async def` to the end of the function body (decorators excluded). |
| `CC102` | Too many parameters | `WARNING` | `max_parameters = 5` | Parameter count in function signature (`self`/`cls`, `*args`, `**kwargs` included; `/` and `*` separators excluded). |
| `CC103` | Too many return statements | `WARNING` | `max_returns = 5` | `return` statements in the function's own scope only. |
| `CC104` | Too many local variables | `WARNING` | `max_locals = 10` | Distinct non-parameter, non-`global`, non-`nonlocal` bindings in the function's own scope via `ScopeProvider`. |
| `CC201` | Class too large | `WARNING` | `max_lines = 200` | Lines from `class` to the end of the class body (decorators excluded). |
| `CC202` | Too many methods | `WARNING` | `max_methods = 15` | Direct methods (including decorated methods) in the class body; dunder methods are counted and reported separately in the message. |
| `CC301` | Excessive nesting | `WARNING` | `max_depth = 4` | Deepest `if`/`for`/`while`/`try`/`with`/`match` nesting in the function's own scope. |
| `CC302` | Excessive boolean operands | `WARNING` | `max_operands = 3` | Operands in the outermost `boolean_operator` chain of an expression; parenthesized inner chains are judged separately. |
| `CC303` | Excessive branching | `WARNING` | `max_branches = 10` | Own-scope decision points (`if`, `elif`, `for`, `while`, `and`/`or`, ternary `x if c else y`, and `match` `case` clauses). |

## Own-scope isolation and Rude's `C901`

- Measurements for `CC103`, `CC104`, `CC202`, `CC301`, and `CC303` never descend
  into nested functions, nested classes, or lambdas; each nested definition is
  evaluated independently.
- `CC301`–`CC303` complement Rude's built-in `C901` (McCabe cyclomatic
  complexity) by measuring control depth, boolean chain length, and own-scope
  decision count without base-`1` or nested-function aggregation. When combining
  both (`select = ["E", "F", "C901", "CC1", "CC2", "CC3"]`), consumers may ignore
  either `CC303` or `C901` depending on which branch metric they prefer.

# Rude Clean Code

Clean Code plugin for the [Rude](https://pypi.org/project/rude/) Python linter,
exposing 59 Clean Code rules across module structure, functions, classes,
complexity, error handling, naming/literals, same-file DRY, SOLID/coupling
indicators, config-driven architecture and pattern boundaries, and
documentation/comment hygiene (`CC001`–`CC910`) through Rude's `rude.plugins`
entry point.

## Quickstart

Install alongside Rude (discovered automatically via `rude.plugins`):

```sh
pip install rude-clean-code
```

Configure profiles and rule options in `pyproject.toml`:

```toml
[tool.rude]
# Basic (CC0-CC3), Strict heuristics (CC4-CC6), and opt-in Architecture (CC7-CC8)
select = ["CC0", "CC1", "CC2", "CC3"]

[tool.rude.rules.CC101]
max_lines = 30

# Optional architecture rules remain inert until you declare your own paths:
[[tool.rude.rules.CC704.forbidden]]
from_paths = ["src/myapp/domain/"]
forbidden_modules = ["sqlalchemy", "myapp.infra"]
```

Run Rude from the command line:

```sh
rude check --select CC0,CC1,CC2,CC3 src/
```

## Working principles

- **Own-scope isolation:** Function and class metrics (`CC101`–`CC104`,
  `CC202`, `CC301`–`CC303`, `CC310`, `CC601`) never leak nested functions,
  classes, or lambdas into an enclosing scope.
- **No unsafe autofixes:** Rules report measured values, limits, and
  remediation hints rather than rewriting business logic.
- **Explicit severity split:** Deterministic, structural, boundary, and doc
  hygiene rules emit `WARNING` (`CC002` and `CC805` emit `INFO`), while
  subjective smell and comment indicators (`CC105`–`CC106`, `CC108`,
  `CC204`–`CC206`, `CC304`–`CC305`, `CC307`, `CC401`–`CC402`, `CC503`,
  `CC601`–`CC605`, `CC902`, `CC904` experimental, `CC909`) emit `INFO`.
- **Inert opt-in architecture checks:** `CC7xx` and `CC8xx` emit zero
  diagnostics unless configured with your modules, classes, and layer paths.

## Implemented rules

- **Modules (`CC0xx`)**: `CC001` (`max_lines = 400`), `CC002` (`__init__.py`
  contains runtime logic), `CC003` (`__init__.py` missing `__all__`), `CC004`
  (deep relative import, `max_relative_depth = 2`), `CC005` (private symbol
  exported in `__all__`)
- **Functions (`CC1xx`)**: `CC101` (`max_lines = 30`), `CC102`
  (`max_parameters = 5`), `CC103` (`max_returns = 5`), `CC104`
  (`max_locals = 10`), `CC105` (boolean flag parameter, `INFO`), `CC106`
  (unused parameter, `INFO`), `CC107` (unused private helper), `CC108` (data
  clump in signatures, `INFO`)
- **Classes (`CC2xx`)**: `CC201` (`max_lines = 200`), `CC202`
  (`max_methods = 15`), `CC204` (`max_dependencies = 5`, `INFO`), `CC205`
  (disjoint responsibility clusters, `INFO`), `CC206` (`max_public_methods = 10`,
  `INFO`), `CC207` (`max_bases = 3`)
- **Complexity and error handling (`CC3xx`)**: `CC301` (`max_depth = 4`),
  `CC302` (`max_operands = 3`), `CC303` (`max_branches = 10`), `CC304`
  (complex expression, `INFO`), `CC305` (single-impl abstraction, `INFO`),
  `CC306` (nested ternary), `CC307` (inverted conditional with `else`, `INFO`),
  `CC308` (`global` statement), `CC309` (broad exception swallowed), `CC310`
  (missing exception chaining), `CC311` (`max_lines = 20`)
- **In-file heuristics (`CC4xx`–`CC6xx`, Strict profile)**: `CC401`
  (unclear function name), `CC402` (unclear class/variable name), `CC403`
  (repeated magic literal, `min_occurrences = 3`), `CC501` (duplicate function
  body within the **same file**, `min_lines = 5`; cross-file duplication is
  planned as `CC502`), `CC503` (repeated validation guards, `INFO`), `CC504`
  (repeated file-scope constants, `WARNING`), `CC601` (repeated type switch,
  `INFO`), `CC602` (suspicious override, `INFO`), `CC603` (ISP indicator,
  `INFO`), `CC604` (chained access, `INFO`), `CC605` (external private member
  access, `INFO`)
- **Architecture and dependencies (`CC7xx`, opt-in config)**: `CC701`
  (forbidden concrete imports), `CC702` (concrete instantiation in domain code),
  `CC704` (general forbidden layer dependencies)
- **Design-pattern boundaries (`CC8xx`, opt-in config)**: `CC801` (data access
  outside repository layer), `CC802` (product instantiated outside factory),
  `CC803` (strategy class violating protocol), `CC804` (handler missing
  registration decorator), `CC805` (concrete service construction bypassing
  dependency injection, `INFO`)
- **Documentation and comments (`CC9xx`)**: `CC901` (public API missing
  docstring), `CC902` (commented-out code, `INFO`), `CC903` (TODO/FIXME without
  reference, expiry, or forbidden markers), `CC904` (comment restating code,
  experimental `INFO`), `CC905` (empty TODO), `CC906` (blanket or unexplained
  suppressions), `CC907` (placeholder docstring), `CC908` (docstring parameter
  drift), `CC909` (docstring return/yield mismatch, `INFO`), `CC910` (dangling
  body string literal)

The package initializer `rude_clean_code` exposes only `VERSION` (read from
installed distribution metadata); plugin rules live in `rude_clean_code.plugin`.

See the
[repository README](https://github.com/Archont561/rude-clean-code#readme) and
[rule reference](https://github.com/Archont561/rude-clean-code/blob/main/docs/reference/rules.md)
for full detection contracts, configuration options, and the backlog roadmap.

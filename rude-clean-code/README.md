# Rude Clean Code

Clean Code plugin for the [Rude](https://pypi.org/project/rude/) Python linter,
exposing 34 Clean Code rules across module structure, functions, classes,
complexity, error handling, naming/literals, same-file duplication,
polymorphism indicators, and config-driven architecture and pattern boundaries
(`CC001`–`CC805`) through Rude's `rude.plugins` entry point.

## Installation

```sh
pip install rude-clean-code
```

Rude discovers the plugin automatically via `rude.plugins` once installed.

## Configuration profiles

Add the **Basic** profile snippet (`CC0`–`CC3`) to your `pyproject.toml`,
include `"CC4"`, `"CC5"`, `"CC6"` for the **Strict** profile with heuristic
indicators, or include `"CC7"`, `"CC8"` for opt-in **Architecture** and
design-pattern boundary rules (inert until configured):

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3"]

[tool.rude.rules.CC101]
max_lines = 30
```

Run Rude from the command line:

```sh
rude check --select CC0,CC1,CC2,CC3 src/
```

All `CC0xx`–`CC3xx`, `CC7xx`, and `CC801`–`CC804` rules (except `CC002` at
`INFO`), plus `CC403` and `CC501`, report `WARNING` severity; `CC002`,
`CC805`, and subjective indicator rules (`CC401`, `CC402`, `CC601`) report
`INFO`.

## Implemented rules

- **Modules (`CC0xx`)**: `CC001` (`max_lines = 400`), `CC002` (`__init__.py`
  contains runtime logic), `CC003` (`__init__.py` missing `__all__`), `CC004`
  (deep relative import, `max_relative_depth = 2`), `CC005` (private symbol
  exported in `__all__`)
- **Functions (`CC1xx`)**: `CC101` (`max_lines = 30`), `CC102`
  (`max_parameters = 5`), `CC103` (`max_returns = 5`), `CC104`
  (`max_locals = 10`), `CC107` (unused private helper)
- **Classes (`CC2xx`)**: `CC201` (`max_lines = 200`), `CC202`
  (`max_methods = 15`), `CC207` (`max_bases = 3`)
- **Complexity and error handling (`CC3xx`)**: `CC301` (`max_depth = 4`),
  `CC302` (`max_operands = 3`), `CC303` (`max_branches = 10`), `CC306`
  (nested ternary), `CC308` (`global` statement), `CC309` (broad exception
  swallowed), `CC310` (missing exception chaining), `CC311` (`max_lines = 20`)
- **In-file heuristics (`CC4xx`–`CC6xx`, Strict profile)**: `CC401`
  (unclear function name), `CC402` (unclear class/variable name), `CC403`
  (repeated magic literal, `min_occurrences = 3`), `CC501` (duplicate function
  body within the **same file**, `min_lines = 5`; cross-file duplication is
  planned as `CC502`), `CC601` (repeated `isinstance`/attribute switch,
  `min_isinstance = 3`)
- **Architecture and dependencies (`CC7xx`, opt-in config)**: `CC701`
  (forbidden concrete imports), `CC702` (concrete instantiation in domain code),
  `CC704` (general forbidden layer dependencies)
- **Design-pattern boundaries (`CC8xx`, opt-in config)**: `CC801` (data access
  outside repository layer), `CC802` (product instantiated outside factory),
  `CC803` (strategy class violating protocol), `CC804` (handler missing
  registration decorator), `CC805` (concrete service construction bypassing
  dependency injection, `INFO`)

The package initializer `rude_clean_code` exposes only `VERSION` (read from
installed distribution metadata); plugin rules live in `rude_clean_code.plugin`.

See the
[repository README](https://github.com/Archont561/rude-clean-code#readme) and
[rule reference](https://github.com/Archont561/rude-clean-code/blob/main/docs/reference/rules.md)
for full detection contracts, configuration options, and the backlog roadmap.

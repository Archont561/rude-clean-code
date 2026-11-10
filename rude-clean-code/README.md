# Rude Clean Code

Clean Code plugin for the [Rude](https://pypi.org/project/rude/) Python linter,
exposing deterministic size, parameter, scope, and complexity rules
(`CC101`–`CC104`, `CC201`–`CC202`, `CC301`–`CC303`) through Rude's
`rude.plugins` entry point.

## Installation

```sh
pip install rude-clean-code
```

Rude discovers the plugin automatically via `rude.plugins` once installed.

## Basic profile

Add the **Basic** profile snippet to your `pyproject.toml`:

```toml
[tool.rude]
select = ["CC1", "CC2", "CC3"]

[tool.rude.rules.CC101]
max_lines = 30
```

Run Rude from the command line:

```sh
rude check --select CC src/
```

All deterministic core rules report `WARNING` severity with measured value,
configured limit, and a suggested refactoring action.

## Implemented rules

- **Functions (`CC1xx`)**: `CC101` (`max_lines = 30`), `CC102`
  (`max_parameters = 5`), `CC103` (`max_returns = 5`), `CC104`
  (`max_locals = 10`)
- **Classes (`CC2xx`)**: `CC201` (`max_lines = 200`), `CC202`
  (`max_methods = 15`)
- **Complexity (`CC3xx`)**: `CC301` (`max_depth = 4`), `CC302`
  (`max_operands = 3`), `CC303` (`max_branches = 10`)

The package initializer `rude_clean_code` exposes only `VERSION` (read from
installed distribution metadata); plugin rules live in `rude_clean_code.plugin`.

See the
[repository README](https://github.com/Archont561/rude-clean-code#readme) and
[rule reference](https://github.com/Archont561/rude-clean-code/blob/main/docs/reference/rules.md)
for full detection contracts, configuration options, and the backlog roadmap.

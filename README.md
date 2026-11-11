<h1 align="center">Welcome to Rude Clean Code 👋</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-0.3.0-blue.svg?cacheSeconds=2592000" />
  <a href="docs/README.md" target="_blank">
    <img alt="Documentation" src="https://img.shields.io/badge/documentation-yes-brightgreen.svg" />
  </a>
  <a href="https://github.com/Archont561/rude-clean-code/graphs/commit-activity" target="_blank">
    <img alt="Maintenance" src="https://img.shields.io/badge/Maintained%3F-yes-green.svg" />
  </a>
  <a href="https://github.com/Archont561/rude-clean-code/blob/main/LICENSE" target="_blank">
    <img alt="License: MIT" src="https://img.shields.io/github/license/Archont561/rude-clean-code" />
  </a>
</p>

> Clean Code plugin for the Rude Python linter. Implements 59 rules across modules, functions, classes, complexity, error handling, naming/literals, same-file DRY, SOLID/coupling indicators, config-driven architecture and pattern boundaries, and documentation/comment hygiene (`CC001`–`CC910`); only the three project-wide rules (`CC203`, `CC502`, `CC703`) remain planned.

### 🏠 [Homepage](https://github.com/Archont561/rude-clean-code#readme)

## Quickstart

### 1. Install

```sh
pip install rude-clean-code
```

Rude discovers the `rude.plugins` entry point automatically once installed.

### 2. Configure `pyproject.toml`

Rude has no built-in preset flag, so select rule families explicitly under
`[tool.rude]`. Start with the **Basic** profile (`CC0`–`CC3` deterministic
rules), optionally enable **Strict** heuristics (`CC105`–`CC605`),
**Documentation** (`CC9`), or configure **Architecture** boundaries
(`CC7`–`CC8`) using your own modules, classes, and paths:

```toml
[tool.rude]
# Basic (CC0-CC3 deterministic) + Strict heuristics (CC4-CC6) + Architecture (CC7-CC8) + Docs (CC9)
select = ["CC0", "CC1", "CC2", "CC3", "CC4", "CC5", "CC6", "CC7", "CC8", "CC9"]

# Tune deterministic limits (examples show defaults):
[tool.rude.rules.CC101]
max_lines = 30

[tool.rude.rules.CC103]
max_returns = 5

# Opt-in layer & pattern boundaries (adapt placeholder names to your repo):
[[tool.rude.rules.CC704.forbidden]]
from_paths = ["src/myapp/domain/"]
forbidden_modules = ["sqlalchemy", "myapp.infra"]

[tool.rude.rules.CC801]
data_modules = ["sqlalchemy"]
repository_paths = ["src/myapp/repositories/"]

[tool.rude.rules.CC805]
service_classes = ["EmailNotifier"]
exclude_paths = ["src/myapp/composition.py"]
```

### 3. Run

```sh
# Basic profile only:
rude check --select CC0,CC1,CC2,CC3 src/

# All configured rules from pyproject.toml:
rude check src/
```

Warnings (`WARNING`) and indicators (`INFO`) report measured values, limits,
and remediation hints without breaking builds unless you fail on warnings.

## How the rules work

Every rule runs per file on Rude's tree-sitter AST and `ScopeProvider` without
unsafe autofixes, and falls into one of three working principles:

| Profile | Families | Severity | Working principle |
| --- | --- | --- | --- |
| **Basic** | Deterministic `CC0xx`–`CC3xx` | `WARNING` (`CC002` is `INFO`) | Size, structure, and fail-fast checks scoped strictly to one function or class (`max_*` options) |
| **Strict** | `CC4xx`–`CC6xx` + heuristic `CC1xx`–`CC3xx` | `INFO` (`CC403`, `CC501`, `CC504` are `WARNING`) | In-file maintainability smells: flags, clumps, cohesion, expressions, names, clones, and SOLID/coupling indicators |
| **Architecture** | `CC7xx`–`CC8xx` | `WARNING` (`CC805` is `INFO`) | **Inert until configured**: enforces layer and pattern boundaries only for modules, classes, and paths you declare |
| **Documentation** | `CC9xx` | `WARNING` (`CC902`, `CC904`, `CC909` are `INFO`) | Public API docstrings, parameter/return drift, dangling strings, commented-out code, tracked `TODO` comments, and suppressions |

### Representative rule examples

#### 1. Own-scope isolation (`CC103`, `CC301`–`CC303` — Basic)

Counts never leak from nested helper functions, nested classes, or lambdas
into an enclosing function, so extracting cohesive helpers shrinks complexity
without false inflation:

```python
def evaluate(items, flag):        # CC103 counts 3 outer returns (not 5)
    def classify(value):          # Measured independently as 2 returns
        if value > 10:
            return "high"
        return "low"

    if not items:
        return "empty"
    if flag:
        return "flagged"
    return classify(len(items))
```

With `[tool.rude.rules.CC103] max_returns = 2`:

```text
dispatch.py:1:0: CC103 Function 'evaluate' has too many return statements (3 > 2); simplify control flow or extract helpers
```

#### 2. Fail-fast error handling (`CC309`, `CC310`, `CC311` — Basic)

Structural rules catch error-handling mistakes from AST shape and semantic
context, such as swallowed broad `except` blocks (`CC309`), missing
`raise ... from err` chaining (`CC310`), and oversized `try:` blocks (`CC311`):

```python
def load_safely(dsn):
    try:
        return open_session(dsn)
    except Exception:
        pass
```

```text
orders.py:4:4: CC309 Broad exception handler (Exception) swallows error via 'pass'; catch specific exceptions, log or re-raise, or use contextlib.suppress
```

#### 3. In-file maintainability indicators (`CC501`, `CC601` — Strict)

Heuristic rules highlight refactor candidates inside a single file while
leaving design judgment to you: `CC501` hashes normalized function bodies to
flag same-file clones, and `CC601` spots repeated `isinstance(...)` or
attribute-switch dispatch (`INFO`):

```python
def render(shape):
    if isinstance(shape, Circle):
        return shape.radius
    if isinstance(shape, Square):
        return shape.side
    if isinstance(shape, Triangle):
        return shape.base
    return 0
```

```text
dispatch.py:1:0: CC601 Function 'render' makes 3 (>= 3) isinstance() checks, indicating possible missing polymorphism or strategy dispatch (see also CC803)
```

#### 4. Opt-in architecture & pattern boundaries (`CC701`–`CC704`, `CC801`–`CC805`)

All `CC7xx` and `CC8xx` rules produce **zero diagnostics** until configured,
never require adopting a design pattern, and spare legitimate locations
(`repositories/`, `factories/`, `composition.py`, `create_*` functions):

```python
# src/myapp/domain/orders.py  -> flagged by CC704 and CC801
from sqlalchemy.orm import Session

# src/myapp/repositories/sql_repo.py -> clean under CC704 and CC801
from sqlalchemy.orm import Session
```

```text
src/myapp/domain/orders.py:1:0: CC704 Forbidden import 'sqlalchemy.orm' (matches 'sqlalchemy') in paths matching src/myapp/domain/; depend on a domain abstraction or port instead
src/myapp/domain/orders.py:1:0: CC801 Data access import 'sqlalchemy.orm' (matches 'sqlalchemy') outside configured repository paths; encapsulate persistence inside a repository
```

See [Rules and configuration profiles](docs/reference/rules.md) for all 59
rules, option defaults, and the full Basic, Strict, Documentation, and
Architecture profile TOML templates.

## Documentation

The [`docs/`](docs/README.md) directory is the source of truth for using and
working on this repository:

- [Documentation index](docs/README.md) — everything, organized by purpose
- [Rules and configuration profiles](docs/reference/rules.md) — implemented `CC001`–`CC910` rules, Basic/Strict/Documentation/Architecture profiles, options, and TOML configuration
- [Development setup](docs/guides/development-setup.md) — clone, restore the locked developer sandbox, install hooks
- [Running the checks](docs/guides/running-the-checks.md) — the CI suite locally
- [Python version compatibility](docs/guides/python-version-compatibility.md) — testing against 3.11–3.13 with tox (local and CI)
- [Releasing to PyPI and GitHub](docs/guides/releasing.md) — tag-triggered PyPI trusted publishing and GitHub Releases
- [Pixi and doit tasks](docs/reference/pixi-tasks.md) — the locked task catalogue
- [Repository layout](docs/reference/repository-layout.md) — what lives where and why
- [Scaffold history and root namespace](docs/concepts/version-only-scaffold.md) — why `__init__.py` still exports only `VERSION`
- [Architecture overview](docs/architecture/overview.md) — components and how they fit together
- [Documentation standard](docs/development/documentation.md) — how documentation is maintained here

The [backlog](backlog/README.md) tracks remaining planned work; the
specification (`backlog/docs/`) and decisions (`backlog/decisions/`) describe
the full roadmap. Only the three project-wide rules (`CC203`, `CC502`,
`CC703`) remain planned, not shipped.

## Development & tests

```sh
pixi install --locked
pixi run --locked doit test
pixi run --locked doit ci
```

To inspect the installed package version (read from distribution metadata):

```python
from rude_clean_code import VERSION

print(VERSION)
```

## Author

👤 **Archont561**

- GitHub: [@Archont561](https://github.com/Archont561)

## 🤝 Contributing

Contributions, issues and feature requests are welcome!<br />Feel free to check [issues page](https://github.com/Archont561/rude-clean-code/issues). You can also take a look at the [contributing guide](https://github.com/Archont561/rude-clean-code/blob/main/CONTRIBUTING.md).

## Show your support

Give a ⭐️ if this project helped you!

## 📝 License

Copyright © 2026 [Archont561](https://github.com/Archont561).<br />
This project is [MIT](https://github.com/Archont561/rude-clean-code/blob/main/LICENSE) licensed.

***
_This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator)_

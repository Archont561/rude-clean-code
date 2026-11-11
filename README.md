<h1 align="center">Welcome to Rude Clean Code 👋</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-0.2.0-blue.svg?cacheSeconds=2592000" />
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

> Clean Code plugin for the Rude Python linter. Implements 34 rules across modules, functions, classes, complexity, error handling, naming/literals, same-file DRY, polymorphism indicators, and config-driven architecture and pattern boundaries (`CC001`–`CC805`); remaining rule families (`CC203`, `CC502`, `CC703`, `CC9xx`) remain planned.

### 🏠 [Homepage](https://github.com/Archont561/rude-clean-code#readme)

## Documentation

The [`docs/`](docs/README.md) directory is the source of truth for using and
working on this repository:

- [Documentation index](docs/README.md) — everything, organized by purpose
- [Rules and configuration profiles](docs/reference/rules.md) — implemented `CC001`–`CC805` rules, Basic/Strict/Architecture profiles, options, and TOML configuration
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
the full roadmap. Remaining heuristic, documentation, and project-wide rules
(`CC203`, `CC502`, `CC703`, `CC9xx`) remain planned, not shipped.

## Install

For development in this repository:

```sh
pixi install --locked
```

For consumers installing the plugin alongside Rude:

```sh
pip install rude-clean-code
```

## Usage

Add the **Basic** profile snippet (`CC0`–`CC3`) to your project's
`pyproject.toml` (add `"CC4"`–`"CC6"` for the **Strict** profile, and `"CC7"`–`"CC8"`
with project-specific config for the **Architecture** profile):

```toml
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3"]

[tool.rude.rules.CC101]
max_lines = 30
```

Then run Rude (it discovers `rude-clean-code` via the `rude.plugins` entry point):

```sh
rude check --select CC0,CC1,CC2,CC3 src/
```

See [Rules and configuration profiles](docs/reference/rules.md) for the full
option reference. To inspect the installed package version (read from distribution
metadata):

```python
from rude_clean_code import VERSION

print(VERSION)
```

## Run tests

```sh
pixi run --locked doit test
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

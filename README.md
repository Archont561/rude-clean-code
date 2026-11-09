<h1 align="center">Welcome to Rude Clean Code 👋</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-0.1.0-blue.svg?cacheSeconds=2592000" />
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

> Early-stage, planned Clean Code / SOLID-inspired plugin for the Rude Python linter. Currently a version-only scaffold: the package exposes VERSION only; no lint rules are implemented yet.

### 🏠 [Homepage](https://github.com/Archont561/rude-clean-code#readme)

## Documentation

The [`docs/`](docs/README.md) directory is the source of truth for using and
working on this repository:

- [Documentation index](docs/README.md) — everything, organized by purpose
- [Development setup](docs/guides/development-setup.md) — clone, restore the locked developer sandbox, install hooks
- [Running the checks](docs/guides/running-the-checks.md) — the CI suite locally
- [Python version compatibility](docs/guides/python-version-compatibility.md) — testing against 3.11–3.13 with tox (auxiliary)
- [Pixi tasks](docs/reference/pixi-tasks.md) — the locked task catalogue
- [Repository layout](docs/reference/repository-layout.md) — what lives where and why
- [Version-only scaffold](docs/concepts/version-only-scaffold.md) — why the package exposes only `VERSION`
- [Architecture overview](docs/architecture/overview.md) — components and how they fit together
- [Documentation standard](docs/development/documentation.md) — how documentation is maintained here

The [backlog](backlog/README.md) tracks planned work; the specification
(`backlog/docs/`) and its decisions (`backlog/decisions/`) describe the
planned design. Planned capabilities are not implemented capabilities — no
lint rules exist yet.

## Install

```sh
pixi install --locked
```

## Usage

```sh
pixi run --locked test
```

## Run tests

```sh
pixi run --locked test
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

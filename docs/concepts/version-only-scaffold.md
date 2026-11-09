# The version-only scaffold

Rude Clean Code is an early-stage, planned Clean Code / SOLID-inspired
**plugin for the Rude Python linter**. The repository does not implement any
lint rules yet, and nothing here should be read as if it did. The product
intent, the planned rule catalogue, and the severity contract live in the
backlog:

- Product and architecture specification:
  [`backlog/docs/doc-1 - Rude-Clean-Code-product-and-architecture-specification.md`](../../backlog/docs/doc-1%20-%20Rude-Clean-Code-product-and-architecture-specification.md)
- Proposed rule catalogue and detection contracts:
  [`backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md`](../../backlog/docs/doc-2%20-%20Proposed-rule-catalogue-and-detection-contracts.md)

## What exists today

A single package at the repository root that exposes exactly one
public name:

```python
from importlib.metadata import version as _version

VERSION = _version("rude-clean-code")

__all__ = ["VERSION"]
```

`VERSION` is the installed distribution's version. The source of truth is
the package's `pyproject.toml` (`version = "0.1.0"`): Hatchling parses it at
build time and stamps it into the distribution metadata, which `VERSION`
reads back at import time. Nothing else is exported, and `importlib.metadata`
is patched in the BDD tests to prove the value is genuinely read from
metadata (not a literal in source).

## Why version-only

The constraint is deliberate, not an accident of an unfinished codebase:

- **One distribution, one Python package** — the project ships a single
  artifact named `rude-clean-code`
  ([decision-1](../../backlog/decisions/decision-1%20-%20Ship-one-rude-clean-code-distribution-for-the-plugin.md)).
- **VERSION comes from installed distribution metadata** — callers can rely
  on it without a second, drift-prone copy of the version string in source
  ([decision-2](../../backlog/decisions/decision-2%20-%20Expose-only-VERSION-from-package-initializers.md)).
- **Features and tests stay package-local** — the owning package keeps its
  source, features, and tests together
  ([decision-3](../../backlog/decisions/decision-3%20-%20Keep-features-and-tests-package-local.md)).
- **The package stays a version-only scaffold** until a backlog task
  deliberately relaxes it
  ([decision-4](../../backlog/decisions/decision-4%20-%20Keep-the-package-a-version-only-scaffold.md)).

The practical effect: installing the package is safe and meaningful today
(`pip install .`), and the version contract is
tested end to end, before any rule exists.

## Verifying the contract

```sh
pixi run --locked doit test
```

The BDD feature (`features/package_version.feature`) asserts, from a fresh
interpreter, that `VERSION` is the only public export, that it equals the
`pyproject.toml` version and the installed distribution metadata, that it is
read from metadata, and that the package contains no other source files.
Coverage must stay at or above the threshold in `.coveragerc` (91%).

## What "done" will mean for the first rule

Implementing the first deterministic rule (milestone m-1, task RCC-2)
requires a backlog task, a failing scenario, and a failing test first — see
[CONTRIBUTING.md](../../CONTRIBUTING.md) and the
[architecture overview](../architecture/overview.md). Until then, the honest
status of this repository is: **version-only scaffold, no lint rules
implemented.**

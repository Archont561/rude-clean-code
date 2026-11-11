# Scaffold history and root namespace

Rude Clean Code began as a deliberate **version-only scaffold** (`RCC-1` /
[decision-4](../../backlog/decisions/decision-4%20-%20Keep-the-package-a-version-only-scaffold.md))
until the first deterministic rules were implemented and verified against Rude
in `RCC-2` (`m-1`). `decision-4` is now deliberately superseded by `RCC-2`:
the package implements 26 Clean Code rules (`CC001`–`CC601`), while keeping
the lazy `VERSION`-only root initializer from
[decision-2](../../backlog/decisions/decision-2%20-%20Expose-only-VERSION-from-package-initializers.md).

The full roadmap and remaining planned rule families live in the backlog:

- Product and architecture specification:
  [`backlog/docs/doc-1 - Rude-Clean-Code-product-and-architecture-specification.md`](../../backlog/docs/doc-1%20-%20Rude-Clean-Code-product-and-architecture-specification.md)
- Proposed rule catalogue and detection contracts:
  [`backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md`](../../backlog/docs/doc-2%20-%20Proposed-rule-catalogue-and-detection-contracts.md)
- Implemented rule reference:
  [Rules and configuration profiles](../reference/rules.md)

## Why `rude_clean_code` still exports only `VERSION`

```python
from importlib.metadata import version as _version

VERSION = _version("rude-clean-code")

__all__ = ["VERSION"]
```

Keeping the root package minimal preserves the original architectural
invariants:

- **One distribution, one Python package** — the project ships a single
  artifact named `rude-clean-code`
  ([decision-1](../../backlog/decisions/decision-1%20-%20Ship-one-rude-clean-code-distribution-for-the-plugin.md)).
- **`VERSION` comes from installed distribution metadata** — callers can rely
  on it without duplicating the version string in source, and importing
  `rude_clean_code` never loads `rude` or executes plugin submodules
  ([decision-2](../../backlog/decisions/decision-2%20-%20Expose-only-VERSION-from-package-initializers.md)).
- **Features and tests stay package-local** — the owning package keeps its
  source, features, unit/property tests, and BDD scenarios together
  ([decision-3](../../backlog/decisions/decision-3%20-%20Keep-features-and-tests-package-local.md)).

## How rules are exposed

Rude discovers rules via the `rude.plugins` entry point pointing at
`rude_clean_code.plugin`, which exports `RULES` (and imports the rule modules
only when Rude loads plugins).

## Verifying the contract

```sh
pixi run --locked doit test
```

The version BDD feature (`rude-clean-code/features/package_version.feature`)
asserts, from a fresh interpreter, that `VERSION` is the only public export,
matches `rude-clean-code/pyproject.toml` and installed distribution metadata,
and does not import `rude` or plugin submodules. The rule BDD feature
(`rude-clean-code/features/deterministic_rules.feature`) verifies entry-point
discovery, prefix selection, configuration overrides, and dogfooding.
Coverage must stay at or above `.coveragerc` (`91%`).

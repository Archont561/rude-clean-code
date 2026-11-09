# Architecture overview

Rude Clean Code is a Python distribution scaffold with a locked developer
environment and a planning-first workflow. This page explains the components
and how they compose. It deliberately does not restate the product design —
that is the backlog specification's job
([doc-1](../../backlog/docs/doc-1%20-%20Rude-Clean-Code-product-and-architecture-specification.md));
this page describes the repository as built.

## The moving parts

```text
                        pyproject.toml (version is the source of truth)
                                   │
                                   ▼  hatchling build
                      wheel + sdist (scripts/check_packages.py)
                                   │
                                   ▼  pip install --no-deps --no-build-isolation
                    installed dist-info METADATA (no editable install)
                                   │
                                   ▼  importlib.metadata.version("rude-clean-code")
                    packages/rude-clean-code/src/rude_clean_code/__init__.py
                                   │
                                   ▼
                              VERSION (the only export)
```

### Components

- **The package** (`packages/rude-clean-code/`) is the only distribution and
  the only product artifact. It is built by hatchling from the `src/` layout
  and exposes `VERSION`, read from installed distribution metadata at import
  time. Its BDD contract lives in `features/package_version.feature` and its
  steps in `tests/`; the tests inspect a fresh interpreter to avoid leakage
  from earlier imports.
- **Repository scripts** (`scripts/`) are tooling, not product code: the
  activation helper (`activate.py` — puts local `src/` directories on
  `PYTHONPATH`), the package builder/validator (`check_packages.py`), the
  sandbox restore (`restore.sh`), and the hook installer
  (`install_hooks.sh`). Their tests live in `scripts/tests/`.
- **The locked workspace** (`pixi.toml` / `pixi.lock`) pins every tool used
  locally and in CI: Python and the lint/test/coverage stack from PyPI, the
  CLI tools (lefthook, bun, convco, actionlint, vale, shellcheck) from
  conda-forge. `bun.lock` pins the Bun-side CLIs (backlog.md,
  markdownlint-cli2, skills).
- **CI** (`.github/workflows/ci.yml`) runs three jobs on every push and pull
  request: `Package tests` (coverage, with a 91% line gate from
  `.coveragerc`), `Policy` (lint, format-check, typecheck, check-packages,
  Vale prose lint, alint repository rules, actionlint, and a convco check of
  the incoming commits), and `Documentation` (markdownlint-cli2 formatting +
  lychee link checking).
- **The backlog** (`backlog/`) is the planning source of truth: the product
  specification (doc-1), the proposed rule catalogue (doc-2), decisions
  (1-5), milestones (m-0..m-5) and tasks (RCC-1..RCC-8). It exists so
  proposed work can be traced to decisions instead of improvised.

## The developer sandbox pipeline

The developer environment is reproducible without hand-installing anything:

1. A push to `main` that touches `pixi.toml`, `pixi.lock`,
   `pixi-sandbox.toml`, or `pixi-sandbox.yml` triggers the
   [Publish developer sandbox](../../.github/workflows/pixi-sandbox.yml)
   workflow.
2. The workflow downloads the pinned `pixi-sandbox` release
   (`v0.9.0`, verified against `SHA256SUMS` from the release) and runs
   `pixi-sandbox pipeline` with the plan from `pixi-sandbox.toml`
   (one bundle, `developer`, environment `default`, platform `linux-64`,
   branch prefix `sandbox/`).
3. The pack is verified against the environment manifest (every restored
   entry checked) and pushed to the `sandbox/developer-linux-64` branch.
4. Any clone can then materialize the identical environment with
   `sh scripts/restore.sh`, which fetches the branch, verifies the
   manifest, and registers `pixi`/`pixi-sandbox` under `$HOME/.local/bin`.

The pack is deterministic and self-verifying, so "works on my machine" is
replaced by "this is the packed environment from the reviewed `main`".

## Change flow

```text
branch -> conventional commits -> pull request
        -> CI: Package tests / Policy / Documentation (all required)
        -> merge to main
        -> (only if Pixi manifests changed) sandbox republishes
```

Commits are Conventional Commits; the changelog is generated from them with
convco (`.versionrc`) rather than edited by hand, and release notes follow
[the documentation standard's](../development/documentation.md) rule that
user-visible changes carry their documentation impact with them.

## Decisions that constrain the design

| Decision | Consequence |
| -------- | -------------------------------------------------------------- |
| decision-1 | One distribution, one package: `rude-clean-code` |
| decision-2 | `VERSION` from installed dist metadata; no version literal |
| decision-3 | Features/tests stay in the owning package |
| decision-4 | VERSION-only until a task deliberately relaxes it |
| decision-5 | Flat CC rule codes with explicit severities (planned) |

See [`backlog/decisions/`](../../backlog/decisions/) for the full texts and
[the version-only scaffold concept](../concepts/version-only-scaffold.md) for
why the scaffold looks the way it does.

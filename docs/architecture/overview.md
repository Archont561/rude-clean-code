# Architecture overview

Rude Clean Code is a Clean Code plugin for the Rude Python linter with a
locked developer environment and a planning-first workflow. This page explains
the components and how they compose. It deliberately does not restate the full
backlog roadmap — that is the specification's job
([doc-1](../../backlog/docs/doc-1%20-%20Rude-Clean-Code-product-and-architecture-specification.md));
this page describes the repository as built.

## The moving parts

```text
                   rude-clean-code/pyproject.toml (version, deps, rude.plugins entry point)
                                   │
                                   ▼  hatchling build
                      wheel + sdist (automation/dodo.py check-packages)
                                   │
                                   ▼  pip install --no-deps --no-build-isolation
                    installed dist-info METADATA + entry_points.txt
                         │                                   │
                         ▼                                   ▼  entry_points(group="rude.plugins")
        rude_clean_code/__init__.py              rude_clean_code/plugin.py (RULES)
                         │                                   │
                         ▼                                   ▼
             VERSION (lazy, no Rude import)       rules/{modules,functions,classes,complexity,errors,naming,dry,heuristics,dependencies,patterns}.py + _scope.py
```

### Components

- **The package** (`rude-clean-code/`) is the only distribution and the
  only product artifact. Built by hatchling from the `src/` layout, its root
  `rude_clean_code/__init__.py` exports only `VERSION` lazily from
  installed metadata (without importing Rude), while the `rude.plugins`
  entry point loads `rude_clean_code.plugin:RULES` containing 34 Clean Code
  rules: 21 deterministic/structural **Basic** rules (`CC001`–`CC005`,
  `CC101`–`CC104`, `CC107`, `CC201`–`CC202`, `CC207`, `CC301`–`CC303`,
  `CC306`, `CC308`–`CC311`), 5 **Strict** in-file heuristic rules
  (`CC401`–`CC403`, `CC501`, `CC601`), and 8 config-driven **Architecture**
  and pattern boundary rules (`CC701`, `CC702`, `CC704`, `CC801`–`CC805`)
  backed by shared helpers in `_scope.py`, `_architecture.py`, and
  `_symbol_matching.py` plus Rude's `ScopeProvider`. Its Gherkin features
  (`features/`) and unit, property, integration, and BDD tests (`tests/`)
  live inside the package.
- **Task automation and bootstrap** (`automation/` and `scripts/`) are tooling,
  not product code: [`automation/dodo.py`](../../automation/dodo.py)
  declares the unified `doit` tasks (configured via root
  [`doit.cfg`](../../doit.cfg) and runnable via `pixi run --locked tools`)
  importing helpers from `automation/lib/` (packaging, git checks, quality
  checks, and Pixi `PYTHONPATH` activation in `activate.py`), with Gherkin
  specs in `automation/features/` and tests in `automation/tests/`.
  `scripts/` contains only the pre-Pixi sandbox restore bootstrap
  (`restore.sh`), enforced by `.alint.yml`.
- **The locked workspace** (`pixi.toml` / `pixi.lock`) pins every tool used
  locally and in CI: Python, `rude`, `hypothesis`, and the lint/test/coverage/
  automation stack (including `doit`) from PyPI, plus CLI tools (lefthook,
  bun, convco, actionlint, vale, shellcheck) from conda-forge. `bun.lock`
  pins the Bun-side CLIs (backlog.md, markdownlint-cli2, skills).
- **CI** (`.github/workflows/ci.yml`) runs on every push and pull
  request: `Package tests` (coverage, with a 91% line gate from
  `.coveragerc`), `Policy` (lint, format-check, typecheck, check-packages,
  Vale prose lint, alint repository rules, actionlint, and a convco check of
  the incoming commits), `Documentation` (markdownlint-cli2 formatting +
  lychee link checking), and a `Python compatibility` matrix
  (3.11/3.12/3.13, `tox` via the committed `tox.ini`).
- **The backlog** (`backlog/`) is the planning source of truth: the product
  specification (doc-1), the proposed rule catalogue (doc-2), decisions
  (1-5), milestones (m-0..m-5) and tasks (RCC-1..RCC-12). It exists so
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
| decision-2 | `VERSION` from installed dist metadata; no version literal or eager Rude import |
| decision-3 | Features/tests stay in the owning package |
| decision-4 | Superseded by `RCC-2` (`m-1`); deterministic rules live in plugin submodules |
| decision-5 | Flat CC rule codes (`CC001`–`CC805`) with explicit `WARNING` / `INFO` severities |

See [`backlog/decisions/`](../../backlog/decisions/) for the full texts and
[the scaffold history concept](../concepts/version-only-scaffold.md) for why
the package root remains `VERSION`-only.

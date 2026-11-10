# Repository layout

What lives where, and the invariants the layout enforces. Invariants marked
**(decision-N)** refer to the locked decisions in
[`backlog/decisions/`](../../backlog/decisions/); they are not suggestions.

## Top level

| Entry                          | Kind        | Purpose                                                        |
| ------------------------------ | ----------- | -------------------------------------------------------------- |
| `rude-clean-code/`             | package     | The only distribution: `rude-clean-code` (`src/`, `features/`, `tests/`, `pyproject.toml`, `README.md`, `LICENSE`) |
| `automation/`                  | automation  | Unified `doit` tasks (`dodo.py`), Gherkin specs (`features/`), and BDD tests (`tests/`) |
| `doit.cfg`                     | automation  | Points `doit` at `automation/dodo.py` from the repository root |
| `scripts/`                     | scripts     | Pre-Pixi sandbox restore (`restore.sh`) and Pixi environment activation (`activate.py`) |
| `scripts/tests/`               | tests       | Tests for repository sandbox configuration                     |
| `backlog/`                     | workspace   | Backlog.md records: spec, decisions 1-5, milestones m-0..m-5, tasks RCC-1..RCC-12 |
| `docs/`                        | docs        | This documentation layer (see [`docs/README.md`](../README.md))  |
| `.agents/skills/`              | vendored    | Upstream agent skills (TDD, BDD, refactor, clean-code)         |
| `.github/`                     | community   | `workflows/` (ci.yml, pixi-sandbox.yml, release.yml), `ISSUE_TEMPLATE/` (bug report, feature request, config), `PULL_REQUEST_TEMPLATE.md`, `dependabot.yml` |
| `.alint/`                      | policy      | JSON Schema consumed by the alint Dependabot policy rule        |
| `.vale/`                       | config      | Vale styles and Project vocabulary                              |
| `pixi.toml`, `pixi.lock`       | lockfile    | Locked linux-64 environment of record                           |
| `pixi-sandbox.toml`            | plan        | Declares what the sandbox publisher packs                       |
| `package.json`, `bun.lock`     | tooling     | Developer CLIs (backlog.md, markdownlint-cli2, skills)          |
| `lefthook.yml`                 | hooks       | pre-commit / commit-msg / pre-push hooks                        |
| `ruff.toml`, `mypy.ini`, `.coveragerc`, `.versionrc` | config | Lint, types, coverage, Conventional Commits    |
| `tox.ini`                       | config      | Committed tox matrix (py311–py313) run by CI    |
| `.alint.yml`                   | policy      | Repository structure rules (`alint check`)                      |
| `.vale.ini`                    | prose       | Vale configuration                                              |
| `codecov.yml`, `skills-lock.json`, `.gitignore`      | misc   | Upload policy, skills pinning, ignores                         |
| `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, `CHANGELOG.md`, `LICENSE` | docs | Entry points and legal             |

## The package

```text
rude-clean-code/
├── LICENSE                              # package MIT license
├── README.md                            # package README for PyPI
├── pyproject.toml                       # version, rude dependency, rude.plugins entry point
├── features/
│   ├── deterministic_rules.feature      # Gherkin contract for CC101-CC303 discovery & CLI
│   └── package_version.feature          # Gherkin contract for lazy VERSION-only __init__.py
├── src/rude_clean_code/
│   ├── __init__.py                      # public root surface: VERSION only
│   ├── _scope.py                        # shared own-scope traversal & threshold rule base
│   ├── plugin.py                        # rude.plugins entry-point module exposing RULES
│   ├── py.typed                         # PEP 561 typed-package marker
│   └── rules/
│       ├── __init__.py                  # rule package marker
│       ├── classes.py                   # CC201-CC202
│       ├── complexity.py                # CC301-CC303
│       └── functions.py                 # CC101-CC104
└── tests/
    ├── test_class_rules.py              # unit & Hypothesis tests for CC201-CC202
    ├── test_complexity_rules.py         # unit & Hypothesis tests for CC301-CC303
    ├── test_deterministic_rules_bdd.py  # pytest-bdd steps for deterministic_rules.feature
    ├── test_function_rules.py           # unit & Hypothesis tests for CC101-CC104
    ├── test_package_version_bdd.py      # pytest-bdd steps for package_version.feature
    ├── test_plugin_discovery.py         # entry-point, prefix select/ignore, & worker config tests
    └── test_scope_traversal.py          # unit & syntax-recovery tests for shared scope helpers
```

- The hatchling sdist ships only `src/`, `tests/`, `features/`, and the
  package `README.md` and `LICENSE` (plus the always-forced
  `pyproject.toml` and PKG-INFO), not the whole repository snapshot.
- Only `VERSION` is exported from `rude_clean_code/__init__.py`, read from
  installed distribution metadata (decision-2). `decision-4` was deliberately
  superseded by `RCC-2` (`m-1`): deterministic rule modules live inside
  `rude_clean_code` and are loaded only when Rude imports the `rude.plugins`
  entry point (`rude_clean_code.plugin`).
- Package behavior, tests, and Gherkin features live inside the owning
  package under `rude-clean-code/` (decision-3). Unified automation tasks
  (`dodo.py`), Gherkin specs (`features/`), and BDD tests (`tests/`) live in
  `automation/` (configured via root `doit.cfg`), pre-Pixi/activation
  scripts live in root `scripts/`, and sandbox/script tests live in
  `scripts/tests/`.

## The workflows

- [`ci.yml`](../../.github/workflows/ci.yml) — `Package tests`
  (coverage), `Policy` (lint, format, types, packages, prose, repo and
  workflow lint, convco), `Documentation` (markdownlint-cli2 and
  lychee), and `Python compatibility` (tox across 3.11–3.13).
  Runs on every push and pull request.
- [`pixi-sandbox.yml`](../../.github/workflows/pixi-sandbox.yml) — republishes
  the locked developer environment to `sandbox/developer-linux-64` on pushes
  to `main` that touch `pixi.toml`, `pixi.lock`, `pixi-sandbox.toml`, or the
  workflow itself.

## Invariants

- The single `rude-clean-code` distribution lives under `rude-clean-code/`
  (`pyproject.toml`, `src/`, `features/`, `tests/`, `README.md`, `LICENSE`),
  while repository automation lives under `automation/`.
- `VERSION` is never duplicated in source; change
  `rude-clean-code/pyproject.toml` instead.
- `pixi.lock` and `bun.lock` are committed. Edit manifests, then regenerate
  (`pixi lock` on a networked machine; `bun install` for `bun.lock`).
- Backlog records are created and edited through `pixi run --locked backlog`,
  never by hand. CI and release notes derive from Conventional Commits.
- `examples/` stays empty until the public API is stable (see
  [CONTRIBUTING.md](../../CONTRIBUTING.md)).
- `CLAUDE.md` is a symlink to `AGENTS.md` (Claude Code does not read
  `AGENTS.md` natively); keep them linked. The marked sections of
  `AGENTS.md` are maintained with `pixi run --locked agents-md`, never by
  hand — see `AGENTS.md`, "How this file is maintained".
- Documentation is maintained continuously (see
  [the documentation standard](../development/documentation.md)).

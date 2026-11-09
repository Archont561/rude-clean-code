# Repository layout

What lives where, and the invariants the layout enforces. Invariants marked
**(decision-N)** refer to the locked decisions in
[`backlog/decisions/`](../../backlog/decisions/); they are not suggestions.

## Top level

| Entry                          | Kind        | Purpose                                                        |
| ------------------------------ | ----------- | -------------------------------------------------------------- |
| `pyproject.toml`, `src/`, `features/`, `tests/` | package | The only distribution: `rude-clean-code` (VERSION-only scaffold), at the repository root |
| `scripts/`                     | scripts     | Repository automation (activation, release build, commit-message check, sandbox restore) |
| `scripts/tests/`               | tests       | Tests for the repository scripts                                |
| `backlog/`                     | workspace   | Backlog.md records: spec, decisions 1-5, milestones m-0..m-5, tasks RCC-1..RCC-8 |
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
(repository root)
├── pyproject.toml                 # name/version source of truth (0.1.0)
├── features/package_version.feature   # Gherkin contract for VERSION
├── src/rude_clean_code/__init__.py    # the entire public surface: VERSION
└── tests/test_package_version_bdd.py  # pytest-bdd steps for the feature
```

- The hatchling sdist ships only `src/`, `tests/`, `features/`, the root
  README and LICENSE (plus the always-forced `pyproject.toml` and PKG-INFO),
  not the whole repository snapshot.
- Only `VERSION` is exported, read from installed distribution metadata
  (decision-2). No other modules, no other exports, no lint rules yet
  (decision-4).
- Package behavior, tests, and Gherkin features live in the root package
  (decision-3). Repository scripts live in root `scripts/` with tests in
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

- The package is the repository root: `pyproject.toml`, `src/`, `features/`,
  and `tests/` at the top level. There is no `packages/` directory.
- `VERSION` is never duplicated in source; change `pyproject.toml` instead.
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

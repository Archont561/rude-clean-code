# Repository layout

What lives where, and the invariants the layout enforces. Invariants marked
**(decision-N)** refer to the locked decisions in
[`backlog/decisions/`](../../backlog/decisions/); they are not suggestions.

## Top level

| Entry                          | Kind        | Purpose                                                        |
| ------------------------------ | ----------- | -------------------------------------------------------------- |
| `rude-clean-code/`             | package     | The only distribution: `rude-clean-code` (`src/`, `features/`, `tests/`, `pyproject.toml`, `README.md`, `LICENSE`) |
| `automation/`                  | automation  | Unified `doit` tasks (`dodo.py`), helper modules (`lib/`), Gherkin specs (`features/`), and tests (`tests/`) |
| `doit.cfg`                     | automation  | Points `doit` at `automation/dodo.py` from the repository root |
| `scripts/`                     | scripts     | Holds only the pre-Pixi sandbox restore bootstrap (`restore.sh`), enforced by `.alint.yml` |
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
│   ├── architecture_and_patterns.feature       # Gherkin contract for CC7xx-CC8xx config & boundaries
│   ├── deterministic_rules.feature             # Gherkin contract for CC001-CC910 discovery & CLI
│   ├── maturing_and_documentation_rules.feature # Gherkin contract for RCC-6/7/11/12 profiles
│   ├── module_rules.feature                    # Gherkin contract for CC001-CC005 module rules
│   └── package_version.feature                 # Gherkin contract for lazy VERSION-only __init__.py
├── src/rude_clean_code/
│   ├── __init__.py                      # public root surface: VERSION only
│   ├── _scope.py                        # shared own-scope traversal & threshold rule base
│   ├── plugin.py                        # rude.plugins entry-point module exposing RULES
│   ├── py.typed                         # PEP 561 typed-package marker
│   └── rules/
│       ├── __init__.py                  # rule package marker
│       ├── _architecture.py             # shared config layer & import matching helpers
│       ├── _comment_analysis.py         # shared AST-comment parse, marker & suppression helpers
│       ├── _docstring_analysis.py       # shared docstring parser & public-API iterator
│       ├── _module_analysis.py          # shared module-level import/side-effect AST helpers
│       ├── _parameter_analysis.py       # shared parameter, stub, and visible-class helpers
│       ├── _symbol_matching.py          # shared call, scope, method, and decorator matchers
│       ├── class_heuristics.py          # CC204-CC206
│       ├── classes.py                   # CC201-CC202, CC207
│       ├── comments.py                  # CC902-CC906
│       ├── complexity.py                # CC301-CC303, CC306, CC308
│       ├── complexity_heuristics.py     # CC304-CC305, CC307
│       ├── coupling_heuristics.py       # CC604-CC605
│       ├── dependencies.py              # CC701, CC702, CC704
│       ├── documentation.py             # CC901, CC907-CC910
│       ├── dry.py                       # CC501 (same-file body duplication)
│       ├── dry_heuristics.py            # CC503-CC504
│       ├── errors.py                    # CC309-CC311
│       ├── function_heuristics.py       # CC105-CC106, CC108
│       ├── functions.py                 # CC101-CC104, CC107
│       ├── heuristics.py                # CC601
│       ├── modules.py                   # CC001-CC005
│       ├── naming.py                    # CC401-CC403
│       ├── patterns.py                  # CC801-CC805
│       └── solid_heuristics.py          # CC602-CC603
└── tests/
    ├── fixtures/consumer_app/           # consumer-shaped fixture layout for CC7xx-CC8xx
    ├── test_architecture_and_patterns_bdd.py # pytest-bdd steps for architecture_and_patterns.feature
    ├── test_class_rules.py              # unit & Hypothesis tests for CC201-CC202
    ├── test_complexity_rules.py         # unit & Hypothesis tests for CC301-CC303
    ├── test_dependency_rules.py         # unit, CLI, & fixture tests for CC701, CC702, CC704
    ├── test_deterministic_rules_bdd.py  # pytest-bdd steps for deterministic_rules.feature
    ├── test_documentation_and_comments.py # unit & regression tests for CC901-CC910
    ├── test_function_rules.py           # unit & Hypothesis tests for CC101-CC104
    ├── test_heuristic_rules.py          # unit & false-positive tests for CC401-CC403, CC501, CC601
    ├── test_maturing_and_documentation_bdd.py # pytest-bdd steps for maturing & CC9xx profiles
    ├── test_maturing_heuristics.py      # unit tests for CC105, CC204-206, CC304-305, CC503-504, CC602-603
    ├── test_module_rules.py             # unit & Hypothesis tests for CC001-CC005
    ├── test_module_rules_bdd.py         # pytest-bdd steps for module_rules.feature
    ├── test_package_version_bdd.py      # pytest-bdd steps for package_version.feature
    ├── test_pattern_rules.py            # unit & fixture tests for CC801-CC805
    ├── test_plugin_discovery.py         # entry-point, prefix select/ignore, & worker config tests
    ├── test_readability_and_coupling.py # unit & exemption tests for CC106, CC108, CC307, CC604-605
    ├── test_scope_traversal.py          # unit & syntax-recovery tests for shared scope helpers
    └── test_structural_and_error_rules.py # unit tests for CC107, CC207, CC306, CC308-CC311
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
  package under `rude-clean-code/` (decision-3). Repository automation lives
  under `automation/` (`dodo.py`, `lib/`, `features/`, and `tests/`,
  configured via root `doit.cfg`), while `scripts/` holds only
  `restore.sh` (enforced by `.alint.yml`).

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

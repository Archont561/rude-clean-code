# Pixi tasks

The locked Pixi workspace (`pixi.toml` + `pixi.lock`) is the environment of
record. Tasks are run as `pixi run --locked <task>`. This page is a
reference — update it in the same change that edits `pixi.toml` (see
[the documentation standard](../development/documentation.md)).

The workspace targets `linux-64` only. Activation prepends the `src/`
directories of tracked or unignored `pyproject.toml` projects to
`PYTHONPATH` ([`scripts/activate.py`](../../scripts/activate.py)).

## Tasks

| Task               | What it runs                                                        | Purpose                                            |
| ------------------ | ------------------------------------------------------------------- | -------------------------------------------------- |
| `install-projects` | `pip install --no-deps --no-build-isolation --force-reinstall ./packages/rude-clean-code` | Install the local wheel without network or build isolation        |
| `test`             | `python -m pytest packages/rude-clean-code/tests`                   | Run the package BDD tests (via `install-projects`) |
| `test-scripts`     | `python -m pytest scripts/tests`                                    | Run the repository script tests                      |
| `coverage`         | `python -m pytest packages/rude-clean-code/tests --cov=... --cov-report=term-missing --cov-report=xml:coverage.xml` | Coverage gate: `.coveragerc` requires ≥ 91% total line coverage |
| `lint`             | `ruff check .`                                                      | Python lint (extends `I`, `PTH`)                     |
| `format-check`     | `ruff format --check .`                                             | Python formatting (diffs fail CI)                    |
| `typecheck`        | `mypy packages/rude-clean-code/src`                                 | Static types (`mypy.ini`)                            |
| `audit`            | `pip-audit --local --skip-editable`                                 | Dependency vulnerability scan (not part of CI)       |
| `check-packages`   | `python scripts/check_packages.py`                                  | Build wheel + sdist, `twine check`, wheel contents   |
| `alint`            | `alint check`                                                       | Repository structure rules from `.alint.yml`         |
| `lint-prose`       | `vale --no-global README.md AGENTS.md CONTRIBUTING.md CHANGELOG.md backlog packages/*/README.md docs` | Vale prose lint; `docs/` and root guides           |
| `docs-lint`        | `bun x --bun --no-install markdownlint-cli2 'README.md' 'AGENTS.md' 'CONTRIBUTING.md' 'CHANGELOG.md' 'docs/**/*.md' 'packages/*/README.md'` | markdownlint-cli2 over maintained markdown (config: `.markdownlint-cli2.jsonc`) |
| `actionlint`       | `actionlint .github/workflows/*.yml`                                | GitHub Actions workflow lint                        |
| `install-hooks`    | `sh scripts/install_hooks.sh`                                       | Install (or validate) lefthook hooks                |
| `hooks-install`    | Alias for `install-hooks`                                           | Backwards compatibility                              |
| `lint-commit`      | `convco check --from-stdin --strip`                                 | Validate a commit message from stdin                |
| `bun-install`      | `bun install --frozen-lockfile`                                     | Install developer tooling from `bun.lock`           |
| `agents-md`        | `bun x --bun --no-install agents-md`                                | Generate and safely refresh the marked sections of `AGENTS.md` (via `bun-install`) |
| `backlog`          | `bun x --bun --no-install backlog`                                  | Backlog.md CLI (via `bun-install`)                  |
| `skills`           | `bun x --bun --no-install skills`                                   | Skills CLI (via `bun-install`)                      |

## Dependency groups

- **Conda (locked in `pixi.lock`)**: Python (`>=3.11,<3.14`), lefthook,
  bun, convco, actionlint, shellcheck, vale.
- **PyPI (locked in `pixi.lock`)**: hatchling, alint, pytest, pytest-bdd,
  pytest-cov, ruff, mypy, build, twine, pip-audit, packaging.
- **Bun (locked in `bun.lock`)**: backlog.md, markdownlint-cli2, skills,
  `@eugeniughelbur/agents-md`.

## Notes

- `test`, `coverage` and `test-scripts` run `install-projects` first where
  applicable; the local project is never an editable Pixi dependency.
- `check-packages` writes wheels and sdists into `distributions/`
  (gitignored; delete it after local inspection).
- The developer sandbox consumed by `scripts/restore.sh` packs exactly this
  environment; see
  [the architecture overview](../architecture/overview.md#the-developer-sandbox-pipeline).

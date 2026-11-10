# Pixi and doit tasks

The locked Pixi workspace (`pixi.toml` + `pixi.lock`) is the environment of
record, and [`automation/dodo.py`](../../automation/dodo.py) (configured via
root [`doit.cfg`](../../doit.cfg)) defines the unified `doit` task CLI.
Run automation tasks with `pixi run --locked doit <task>` (or
`pixi run --locked do <task>`); running `pixi run --locked doit` with no
arguments executes the default `ci` task. This page is a reference — update
it in the same change that edits `pixi.toml` or `automation/dodo.py` (see
[the documentation standard](../development/documentation.md)).

The workspace targets `linux-64` only. Activation prepends the `src/`
directories of tracked or unignored `pyproject.toml` projects to
`PYTHONPATH` ([`scripts/activate.py`](../../scripts/activate.py)).

## `doit` tasks (`automation/dodo.py`)

| Task                    | What it runs                                                                       | Purpose                                                       |
| ----------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `install-projects`      | `python -m pip install --no-deps --no-build-isolation --force-reinstall ./rude-clean-code` | Install the local wheel without network or build isolation    |
| `test`                  | `python -m pytest rude-clean-code/tests`                                           | Run the package BDD tests (via `install-projects`)            |
| `test-scripts`          | `python -m pytest scripts/tests`                                                   | Run the repository sandbox and script tests                   |
| `test-automation`       | `python -m pytest automation/tests`                                                | Run the automation BDD tests against `automation/features/`   |
| `coverage`              | `python -m pytest rude-clean-code/tests --cov=rude-clean-code/src --cov-report=term-missing --cov-report=xml:coverage.xml` | Coverage gate: `.coveragerc` requires ≥ 91% total line coverage |
| `lint`                  | `ruff check .`                                                                     | Python lint (extends `I`, `PTH`)                              |
| `format-check`          | `ruff format --check .`                                                            | Python formatting (diffs fail CI)                             |
| `typecheck`             | `mypy rude-clean-code/src`                                                         | Static types (`mypy.ini`)                                     |
| `audit`                 | `pip-audit --local --skip-editable`                                                | Dependency vulnerability scan (not part of CI)                |
| `check-packages`        | `check_packages()` in `automation/dodo.py`                                         | Build wheel + sdist into `distributions/`, `twine check`, inspect wheel |
| `alint`                 | `alint check`                                                                      | Repository structure rules from `.alint.yml`                  |
| `lint-prose`            | `vale --no-global README.md rude-clean-code/README.md AGENTS.md CONTRIBUTING.md CHANGELOG.md .github/PULL_REQUEST_TEMPLATE.md backlog docs` | Vale prose lint; `docs/`, PR template, backlog, README guides |
| `bun-install`           | `bun install --frozen-lockfile`                                                    | Install frozen Bun developer CLIs from `bun.lock`             |
| `docs-lint`             | `bun x --bun --no-install markdownlint-cli2 ...` (via `bun-install`)               | markdownlint-cli2 over maintained markdown (`.markdownlint-cli2.jsonc`) |
| `actionlint`            | `actionlint .github/workflows/*.yml`                                               | GitHub Actions workflow lint                                  |
| `install-hooks`         | `install_hooks()` in `automation/dodo.py`                                          | Install (or verify) lefthook git hooks                        |
| `lint-commit`           | `convco check --from-stdin --strip`                                                | Validate a commit message from stdin                          |
| `check-commit-messages` | `check_commit_messages()` in `automation/dodo.py`                                  | Validate incoming commit messages in `base..head` with convco |
| `build-release`         | `build_release()` in `automation/dodo.py`                                          | Verify optional `GITHUB_REF_NAME` tag, build `dist/`, `twine check` |
| `pre-commit`            | `lint`, `format-check`, `typecheck`, `lint-prose`, `alint`, `actionlint`, `docs-lint` | Composite task invoked by the lefthook `pre-commit` hook    |
| `policy`                | `lint`, `format-check`, `typecheck`, `check-packages`, `lint-prose`, `alint`, `actionlint` | Composite task matching the local CI `Policy` checks  |
| `docs`                  | `docs-lint`, `lint-prose`                                                          | Local documentation lint checks                               |
| `ci`                    | `policy`, `docs-lint`, `test-scripts`, `test-automation`, `coverage`               | Default `doit` task running the full local CI suite           |

## Direct Pixi tasks (`pixi.toml`)

Pixi exposes the unified runner alias alongside direct pass-through tasks for
the Bun developer CLIs so arbitrary CLI flags (such as `--help`) forward
unchanged:

| Task          | What it runs                                  | Purpose                                                     |
| ------------- | --------------------------------------------- | ----------------------------------------------------------- |
| `do`          | `doit`                                        | Alias for running `automation/dodo.py` tasks (`pixi run --locked do`) |
| `bun-install` | `bun install --frozen-lockfile`               | Install developer tooling from `bun.lock`                   |
| `agents-md`   | `bun x --bun --no-install agents-md`          | Refresh marked sections of `AGENTS.md` (via `bun-install`)  |
| `backlog`     | `bun x --bun --no-install backlog`            | Backlog.md CLI (via `bun-install`)                          |
| `skills`      | `bun x --bun --no-install skills`             | Skills CLI (via `bun-install`)                              |

## Dependency groups

- **Conda (locked in `pixi.lock`)**: Python (`>=3.11,<3.14`), lefthook,
  bun, convco, actionlint, shellcheck, vale.
- **PyPI (locked in `pixi.lock`)**: hatchling, alint, pytest, pytest-bdd,
  pytest-cov, ruff, mypy, build, twine, pip-audit, packaging, tox, doit.
- **Bun (locked in `bun.lock`)**: backlog.md, markdownlint-cli2, skills,
  `@eugeniughelbur/agents-md`.

## Notes

- `test` and `coverage` depend on `install-projects` in
  `automation/dodo.py`; the local project is never an editable Pixi
  dependency.
- `check-packages` writes wheels and sdists into `distributions/`
  (gitignored); `build-release` writes into `dist/` (gitignored). Run
  `pixi run --locked doit clean` to remove generated local build and coverage
  artifacts.
- The developer sandbox consumed by `scripts/restore.sh` packs exactly this
  environment; see
  [the architecture overview](../architecture/overview.md#the-developer-sandbox-pipeline).
- `tox` is available in the locked environment for Python-version
  compatibility checks (see
  [the tox guide](../guides/python-version-compatibility.md)); run it as
  `pixi run --locked tox`.

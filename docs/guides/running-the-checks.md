# Running the checks

The checks below are the same commands CI runs. If they pass locally they
pass in CI ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)).
Run them through the locked `doit` runner in [`automation/dodo.py`](../../automation/dodo.py):

```sh
pixi run --locked doit <task>
```

Running `pixi run --locked doit` (or `pixi run --locked doit ci`) executes
the full local CI sweep (`policy`, `docs-lint`, `test-scripts`,
`test-automation`, and `coverage`).

## The CI suite

The `CI` workflow has four kinds of jobs, and the `Publish developer sandbox`
workflow runs separately on changes to the Pixi manifests (see
[development setup](development-setup.md#how-the-setup-works)).

### `Package tests`

```sh
pixi run --locked doit coverage
```

Installs the local package and runs the package unit, Hypothesis property,
integration, and BDD tests under `rude-clean-code/` with coverage. `.coveragerc`
requires at least 91% total line coverage (`fail_under`).

To dogfood the installed plugin's rules across the entire repository
(`rude-clean-code`, `automation`, and `scripts`) with the `doit` gate:

```sh
pixi run --locked doit dogfood
```

### `Policy`

```sh
pixi run --locked doit dogfood        # Rude CC1-CC3 across repo Python files (fails on any diagnostic)
pixi run --locked doit lint           # dogfood + ruff check .
pixi run --locked doit format-check   # ruff format --check .
pixi run --locked doit typecheck      # mypy rude-clean-code/src
pixi run --locked doit check-packages # build wheels/sdists, twine check, wheel inspection
pixi run --locked doit lint-prose     # vale --no-global README.md ... docs
pixi run --locked doit alint          # repository structure rules (.alint.yml)
pixi run --locked doit actionlint     # workflow syntax and semantics
```

You can run those checks together locally with `pixi run --locked doit policy`.
The same job validates that every incoming commit message is a valid
Conventional Commit (`pixi run --locked doit check-commit-messages`).
Commits that do not parse cannot be merged; see `.versionrc` for the
configured types and scope regex.

### `Python compatibility`

```sh
pixi run --locked tox            # py311, py312, py313 (interpreters from PATH)
```

Runs the same BDD suite in isolated virtual environments, one per supported
Python version, from the committed `tox.ini`. See
[Python version compatibility](python-version-compatibility.md).

### `Documentation`

```sh
bun install --frozen-lockfile    # or: pixi run --locked doit bun-install
bun x --bun --no-install markdownlint-cli2 'README.md' 'AGENTS.md' 'CONTRIBUTING.md' 'CHANGELOG.md' '.github/PULL_REQUEST_TEMPLATE.md' 'docs/**/*.md'
```

The `docs-lint` task wraps this:

```sh
pixi run --locked doit docs-lint
```

It lints the maintained markdown surface with markdownlint-cli2 (rule
configuration: [`.markdownlint-cli2.jsonc`](../../.markdownlint-cli2.jsonc)).
CI additionally checks for broken links with lychee over the same files
(`docs/**` and the root markdown guides). Backlog records
(`backlog/**`) and vendored skills (`.agents/**`) are intentionally out of
scope: backlog files are immutable records and skills are owned upstream.

Vale prose lint and alint enforce the documentation standard's style and
repository conventions; see [the documentation standard](../development/documentation.md)
and [the task reference](../reference/pixi-tasks.md) for the full
catalogue.

## Auxiliary checks

```sh
pixi run --locked doit test            # package tests without coverage
pixi run --locked doit test-scripts    # sandbox and script tests (scripts/tests/)
pixi run --locked doit test-automation # automation BDD tests (automation/tests/)
pixi run --locked doit audit           # pip-audit --local --skip-editable
```

`audit` is not part of CI (it queries PyPI advisories over the network) but
should be run before releases.

## Hooks

`pixi run --locked doit install-hooks` installs the lefthook hooks that map
onto the same tasks: pre-commit runs `doit pre-commit` (lint, format-check,
typecheck, lint-prose, alint, actionlint, and docs-lint); commit-msg runs
`doit lint-commit`; pre-push runs `doit test`.

## When something fails

- **Lint/format**: `ruff check --fix .` and `ruff format .` fix most issues.
- **Typecheck**: `mypy.ini` is the configuration of record; the package is
  typed strictly.
- **Prose lint**: read the Vale diagnostic; vocabulary additions belong in
  `.vale/styles/config/vocabularies/Project/accept.txt`.
- **alint**: the error message names the rule; rules live in `.alint.yml`.
- **markdownlint**: the rule id (for example `MD032`) links to its
  documentation from the error output.
- **lychee**: rerun with `lychee --no-progress <files>` locally after
  installing lychee; fix the URL or, for legitimately unchecked hosts, add an
  `--exclude` flag in `.github/workflows/ci.yml` with a comment explaining why.
- Anything unimplemented or unverifiable must be reported, not worked around.

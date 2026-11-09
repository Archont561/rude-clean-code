# Running the checks

The checks below are the same commands CI runs. If they pass locally they
pass in CI ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)).
Run them through the locked environment:

```sh
pixi run --locked <task>
```

## The CI suite

The `CI` workflow has three jobs, and the `Publish developer sandbox`
workflow runs separately on changes to the Pixi manifests (see
[development setup](development-setup.md#how-the-setup-works)).

### `Package tests`

```sh
pixi run --locked coverage
```

Installs the local package and runs the BDD tests under
packages/rude-clean-code with coverage. `.coveragerc` requires at least 91%
total line coverage (`fail_under`); the current suite sits at 100%.

### `Policy`

```sh
pixi run --locked lint           # ruff check .
pixi run --locked format-check   # ruff format --check .
pixi run --locked typecheck      # mypy packages/rude-clean-code/src
pixi run --locked check-packages # build wheels/sdists, twine check, wheel inspection
pixi run --locked lint-prose     # vale --no-global README.md AGENTS.md ... docs
pixi run --locked alint          # repository structure rules (.alint.yml)
pixi run --locked actionlint     # workflow syntax and semantics
```

The same job validates that every incoming commit message is a valid
Conventional Commit (`convco check`). Commits that do not parse cannot be
merged; see `.versionrc` for the configured types and scope regex.

### `Documentation`

```sh
bun install --frozen-lockfile    # or: pixi run --locked bun-install
bun x --bun --no-install markdownlint-cli2 'README.md' 'AGENTS.md' 'CONTRIBUTING.md' 'CHANGELOG.md' 'docs/**/*.md' 'packages/*/README.md'
```

The `docs-lint` task wraps this:

```sh
pixi run --locked docs-lint
```

It lints the maintained markdown surface with markdownlint-cli2 (rule
configuration: [`.markdownlint-cli2.jsonc`](../../.markdownlint-cli2.jsonc)).
CI additionally checks for broken links with lychee over the same files
(`docs/**`, the root markdown guides, and package READMEs). Backlog records
(`backlog/**`) and vendored skills (`.agents/**`) are intentionally out of
scope: backlog files are immutable records and skills are owned upstream.

Vale prose lint and alint enforce the documentation standard's style and
repository conventions; see [the documentation standard](../development/documentation.md)
and [the Pixi task reference](../reference/pixi-tasks.md) for the full
catalogue.

## Auxiliary checks

```sh
pixi run --locked test          # package tests without coverage
pixi run --locked test-scripts  # tests for the repository scripts (scripts/tests/)
pixi run --locked audit         # pip-audit --local --skip-editable
```

`audit` is not part of CI (it queries PyPI advisories over the network) but
should be run before releases.

## Hooks

`pixi run install-hooks` installs the lefthook hooks that map onto the same
tasks: pre-commit runs lint, format-check, typecheck, lint-prose, alint,
actionlint and docs-lint; commit-msg runs convco, pre-push runs the tests.

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

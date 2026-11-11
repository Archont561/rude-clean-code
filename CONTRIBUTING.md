# Contributing to Rude Clean Code

Thanks for helping build Rude Clean Code. The plugin currently ships the
deterministic core rules (`CC101`–`CC104`, `CC201`–`CC202`,
`CC301`–`CC303`), while heuristic, organization, architecture, and
documentation rules in the backlog remain planned.
Please check the [backlog](backlog/README.md) and relevant decisions
before proposing work, and avoid presenting planned capabilities as
finished.

## Set up

The locked Pixi workspace targets Linux x86-64 (`linux-64`). Install
Pixi (or restore the published sandbox), then:

```sh
pixi install --locked
pixi run --locked doit install-projects
```

The full walkthrough — restoring the published developer sandbox with
`scripts/restore.sh`, finishing the PyPI install, installing hooks, and
troubleshooting — lives in the
[development setup guide](docs/guides/development-setup.md). The local
project is not an editable Pixi dependency; re-run `doit install-projects`
after changing package metadata. Run `pixi run --locked doit install-hooks`
at the start of every session.

## Make a change

1. Review the relevant backlog task, specification, and decisions. Use
   `pixi run backlog` and its task instructions to create or update
   backlog records rather than editing task files directly.
2. Keep product code, tests, and Gherkin features in the owning package
   (`rude-clean-code/src/`, `rude-clean-code/features/`,
   `rude-clean-code/tests/`, with `rude-clean-code/pyproject.toml`).
   Put repository automation tasks in `automation/dodo.py` with helper
   functions in `automation/lib/`, behavior specifications in
   `automation/features/`, and tests in `automation/tests/`. Keep
   `scripts/` strictly to the pre-Pixi sandbox bootstrap (`restore.sh`),
   enforced by `.alint.yml`. For
   user-visible behavior, add a scenario and a failing test first when
   practical.
3. Update the relevant documentation and report any behavior or checks
   that remain unimplemented or unverified. Keep `examples/` empty until
   the public API is stable.

## Checks

Run the checks relevant to your change; the full local CI suite runs with
`pixi run --locked doit` (or `pixi run --locked doit ci`), and individual
checks include:

```sh
pixi run --locked doit lint
pixi run --locked doit format-check
pixi run --locked doit typecheck
pixi run --locked doit check-packages
pixi run --locked doit audit
pixi run --locked doit lint-prose
pixi run --locked doit docs-lint
pixi run --locked doit alint
pixi run --locked doit actionlint
pixi run --locked doit test
pixi run --locked doit coverage
```

CI additionally checks links in the maintained markdown with lychee. See
[running the checks](docs/guides/running-the-checks.md) for what each
check covers and where its configuration lives.

The coverage configuration (`.coveragerc`) requires at least 91% total
line coverage of the package source tree. For a focused run, use
`pixi run --locked doit test`.

## Documentation

Documentation is part of the product. User-visible changes must update the
canonical documents under [`docs/`](docs/README.md), and the documentation
standard in [docs/development/documentation.md](docs/development/documentation.md)
defines what "done" means. If no documentation change is necessary, say so
explicitly in the pull request.

## Pull requests

Use [Conventional Commits](https://www.conventionalcommits.org/) for
commit messages, such as `fix: handle missing input`. The pull request
template ([.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md))
is pre-filled with the checklist; follow it. Open bugs and feature
suggestions through the issue forms in [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/)
(blank issues are disabled). Explain the change, tests, and any
limitations in the pull request. State the documentation impact: which
documents you updated, or why none were needed.

# Contributing to Rude Clean Code

Thanks for helping build Rude Clean Code. The repository is an early
scaffold: the plugin API and lint rules are planned, not implemented.
Please check the [backlog](backlog/README.md) and relevant decisions
before proposing work, and avoid presenting planned capabilities as
finished.

## Set up

The locked Pixi workspace targets Linux x86-64 (`linux-64`). Install
Pixi, clone the repository, and run:

```sh
pixi install --locked
pixi run --locked install-projects
```

The local project is not an editable Pixi dependency. Package test and
coverage tasks install it without build isolation and test the current
source. Re-run `install-projects` after changing package metadata.
Default-environment activation adds `src` directories belonging to
tracked or unignored `pyproject.toml` files to `PYTHONPATH`. Run
`pixi run install-hooks` to check and install the hooks defined in
`lefthook.yml` (agents must do this at session start).

If Pixi itself is missing, restore the published developer sandbox
instead of installing tools by hand: `sh scripts/restore.sh` restores
the locked `default` environment from the `sandbox/developer-linux-64`
branch (plan: `pixi-sandbox.toml`; publisher:
`.github/workflows/pixi-sandbox.yml`) and registers `pixi` as a user
tool under `$HOME/.local/bin`.

## Make a change

1. Review the relevant backlog task, specification, and decisions. Use
   `pixi run backlog` and its task instructions to create or update
   backlog records rather than editing task files directly.
2. Keep product code, tests, and Gherkin features in the owning package
   (`packages/rude-clean-code/`). Put repository scripts and their tests
   under `scripts/` and `scripts/tests/`. For user-visible behavior, add
   a scenario and a failing test first when practical.
3. Update the relevant documentation and report any behavior or checks
   that remain unimplemented or unverified. Keep `examples/` empty until
   the public API is stable.

## Checks

Run the checks relevant to your change; the full CI suite includes:

```sh
pixi run --locked lint
pixi run --locked format-check
pixi run --locked typecheck
pixi run --locked check-packages
pixi run --locked audit
pixi run --locked lint-prose
pixi run --locked alint
pixi run --locked actionlint
pixi run --locked test
pixi run --locked coverage
```

The coverage configuration (`.coveragerc`) requires at least 91% total
line coverage of the package source tree. For a focused run, use
`pixi run --locked test`.

## Pull requests

Use [Conventional Commits](https://www.conventionalcommits.org/) for
commit messages, such as `fix: handle missing input`. Explain the change,
tests, and any limitations in the pull request.

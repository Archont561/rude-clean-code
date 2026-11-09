# Development setup

Task-oriented guide for getting a fresh clone into a working, verified
state. The canonical environment definition is `pixi.toml` / `pixi.lock`;
nothing here substitutes for it.

## Prerequisites

- Linux x86-64 (the locked workspace targets `linux-64` only).
- `git` and network access to GitHub to fetch the repository and, on first
  use, the published sandbox branch.
- No local Pixi installation is required — the published developer sandbox
  provides it (see below).

## Steps

```sh
git clone https://github.com/Archont561/rude-clean-code.git
cd rude-clean-code
sh scripts/restore.sh
export PATH="$HOME/.local/bin:$PATH"
pixi --version
```

`scripts/restore.sh` restores the published developer sandbox from the
`sandbox/developer-linux-64` branch. That branch is republished by the
[Publish developer sandbox](../../.github/workflows/pixi-sandbox.yml) workflow
onto `main` whenever `pixi.toml`, `pixi.lock`, `pixi-sandbox.toml`, or the
workflow itself change. The restore step:

1. Fetches the sandbox branch (depth 1) into a temporary transport directory.
2. Materializes the packed `default` environment into `.pixi/envs/default`
   and verifies every restored file against the recorded manifest.
3. Registers `pixi` and `pixi-sandbox` as user tools under `$HOME/.local/bin`
   and adds that directory to your shell profile.

The restored environment covers the conda-hosted tools (Python, ruff, vale,
lefthook, bun, convco, actionlint, ...). If the PyPI wheel cache is missing,
complete the install once with network access (PyPI must be reachable):

```sh
pixi install --frozen
```

Then install the local package and run the test suite:

```sh
pixi run --locked doit install-projects
pixi run --locked doit test
```

## Install the git hooks

```sh
pixi run --locked doit install-hooks
```

This installs (or validates) the lefthook hooks defined in
[`lefthook.yml`](../../lefthook.yml): pre-commit runs the `pre-commit`
doit task (lint, format-check, typecheck, lint-prose, alint, actionlint,
and docs-lint); commit-msg validates Conventional Commits with convco;
pre-push runs the tests. Hooks use the same locked doit tasks as CI — do
not bypass them; report failures.

## Verify the setup

Run the same commands CI runs (see
[running the checks](running-the-checks.md)):

```sh
pixi run --locked doit lint
pixi run --locked doit test
pixi run --locked doit alint
```

## How the setup works

The default environment's activation script
([`scripts/activate.py`](../../scripts/activate.py)) prepends the `src/`
directories of local, tracked (or unignored) `pyproject.toml` projects to
`PYTHONPATH`, so `import rude_clean_code` resolves to the current source
without an editable install. `pixi run --locked doit install-projects`
installs the wheel without build isolation so `VERSION` reads the right
distribution metadata. The local project is never an editable Pixi
dependency: re-run `doit install-projects` after changing package metadata
([decision-2](../../backlog/decisions/decision-2%20-%20Expose-only-VERSION-from-package-initializers.md)).

## Troubleshooting

- **`scripts/restore.sh` fails to fetch the sandbox branch.** The branch is
  published by the workflow above; if it does not exist yet (fresh repository)
  or you are offline, report the blocker instead of improvising a virtual
  environment. Do not hand-install substitutes for locked tools.
- **`Pixi` on PATH is stale or missing.** Re-open your shell, or run
  `export PATH="$HOME/.local/bin:$PATH"`. To skip registering user tools
  (shared machines), set `PIXI_SANDBOX_USER_TOOLS=skip` before restoring.
- **A different sandbox bundle is needed.** Set `PIXI_SANDBOX_BUNDLE` or
  `PIXI_SANDBOX_BRANCH` (see `pixi-sandbox.toml` for the declared bundles).
  To restore without fetching, set `PIXI_SANDBOX_FETCH=skip` and fetch the
  `refs/heads/sandbox/*` refs yourself first.
- **`pixi run --locked ...` reports the lockfile is stale.** The lock and the
  manifest are out of sync; fix `pixi.toml` and regenerate `pixi.lock` with a
  networked machine (`pixi lock`). Do not edit `pixi.lock` by hand.

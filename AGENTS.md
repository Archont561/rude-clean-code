# Agent instructions

## Start each session with environment and hook setup

Before the backlog survey or project changes, check that Pixi is
available with `command -v pixi`. If it is missing, run
`sh scripts/restore.sh` from the repository root to restore the developer
sandbox (published by `.github/workflows/pixi-sandbox.yml` from the plan
in `pixi-sandbox.toml`), then add the registered user tools to the
current shell's PATH with `export PATH="$HOME/.local/bin:$PATH"` and
verify `pixi --version`. Restore may need access to the sandbox branch
and registers user tools by default. If restore fails or Pixi remains
unavailable, report the blocker rather than claiming setup succeeded or
improvising a venv; this workspace's environment of record is
`pixi.toml` / `pixi.lock`.

Once Pixi is available, run `pixi run install-hooks` at the start of
every session. Do not bypass a failed installation; report the error.

## Start each session with a backlog survey

After environment and hook setup, before planning or changing the
project, survey the backlog:

```sh
pixi run backlog instructions overview
pixi run backlog milestone list --plain
pixi run backlog task list --status "In Progress" --plain
pixi run backlog task list --status "To Do" --plain
```

Read the applicable backlog specification (`backlog/docs/`) and
decisions (`backlog/decisions/`), check the workspace and Git state, and
reconcile the survey with the user's request before selecting work. Do
not let the survey override a direct user request or automatically start
unrelated work.

Use Backlog.md commands to create and update backlog records. Never edit
backlog task, decision, document, or milestone files directly, and never
mark unfinished or unverified work complete.

## Engineering rules

- The package is a **version-only scaffold** (backlog decision-4):
  `packages/rude-clean-code/src/rude_clean_code/` contains only
  `__init__.py` and it exports only `VERSION`. Do not add rules, modules,
  or public exports without a backlog task that deliberately relaxes
  that decision.
- `VERSION` comes from installed distribution metadata built from the
  package's `pyproject.toml` (decision-2). Never hard-code a second copy
  of the version string in source.
- Keep product features and tests in the package that owns the behavior
  (decision-3): `packages/rude-clean-code/{src,features,tests}`.
  Repository scripts live under root `scripts/`, with their tests under
  `scripts/tests/`. There is no root `src/`, root `tests/`, or root
  `pyproject.toml`.
- For user-visible features, write a Gherkin scenario and a failing test
  in the owning package before implementation when practical.
- Run all checks through `pixi run --locked ...`; they are the same
  commands CI runs. Report anything unimplemented or unverified.
- Commits are Conventional Commits (convco, `.versionrc`).
- Do not push, create a pull request, merge, tag, publish, or release
  without explicit user authorization.

# Rude Clean Code documentation

This directory is the user-facing knowledge layer of the repository. It is
the maintained, discoverable source of truth for understanding, using,
configuring, and operating the software. It serves humans and AI agents
alike, and it is held to the standard in
[the documentation standard](development/documentation.md) — documentation is
part of the product.

If a document here disagrees with the code, configuration, or CI workflows,
treat it as a defect and fix it.

## How the documentation is organized

| Area                              | Purpose                                      |
| --------------------------------- | -------------------------------------------- |
| [guides/](guides/)                | Task-oriented instructions and workflows      |
| [concepts/](concepts/)            | Domain concepts and explanations              |
| [reference/](reference/)          | Commands, configuration, and layout reference |
| [architecture/](architecture/)    | System architecture and design                |
| [development/](development/)      | Contribution and development workflows        |

## Where to start

- **New here?** Read the [development setup guide](guides/development-setup.md),
  then [running the checks](guides/running-the-checks.md).
- **Evaluating the project?** Read the
  [version-only scaffold concept](concepts/version-only-scaffold.md) and the
  [architecture overview](architecture/overview.md) first, so you know what
  the repository does (and does not do yet).
- **Cutting a release?** See [Releasing to PyPI](guides/releasing.md) —
  the release workflow, trusted publishing, and the tag/version guard.
- **Changing code or workflows?** The [documentation standard](development/documentation.md)
  defines what "done" means for documentation impact.
- **Checking Python 3.11–3.13 compatibility?** See
  [Python version compatibility with tox](guides/python-version-compatibility.md)
  (auxiliary to the locked Pixi environment).

## Reference

- [Pixi tasks](reference/pixi-tasks.md) — the locked task catalogue used by
  local development and CI.
- [Repository layout](reference/repository-layout.md) — what lives where and
  why, including the invariants the layout enforces.

## Related sources of truth

- [CONTRIBUTING.md](../CONTRIBUTING.md) — the contributor entry point
  (GitHub surfaces it on pull requests).
- [AGENTS.md](../AGENTS.md) — operational instructions for AI agents,
  maintained with [agents-md](https://github.com/eugeniughelbur/agents-md)
  (`pixi run --locked agents-md`); `CLAUDE.md` symlinks to it.
- [CHANGELOG.md](../CHANGELOG.md) — notable changes, generated with convco
  from Conventional Commits.
- [backlog/](../backlog/README.md) — the Backlog.md workspace: the product
  and architecture specification, decisions, milestones, and tasks. Backlog
  records are edited through the `backlog` tooling, never by hand.

## Maintenance

Documentation changes follow the same pull request and CI process as code.
The documentation checks run in the `Documentation` job of the CI workflow
(`.github/workflows/ci.yml`): markdownlint-cli2 for formatting consistency
and lychee for link validity. Vale (`pixi run --locked lint-prose`) and
alint (`pixi run --locked alint`) run in the `Policy` job. See
[running the checks](guides/running-the-checks.md) for details.

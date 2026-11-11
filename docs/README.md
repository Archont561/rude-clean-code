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
| [reference/](reference/)          | Commands, rules, configuration, and layout   |
| [architecture/](architecture/)    | System architecture and design                |
| [development/](development/)      | Contribution and development workflows        |

## Where to start

- **Configuring the plugin?** See
  [Rules and configuration profiles](reference/rules.md) for the **Basic**
  and **Strict** profile TOML snippets and the 26 implemented `CC001`–`CC601`
  rules.
- **New here?** Read the [development setup guide](guides/development-setup.md),
  then [running the checks](guides/running-the-checks.md).
- **Evaluating the project?** Read the
  [architecture overview](architecture/overview.md) and the
  [scaffold history concept](concepts/version-only-scaffold.md) to understand
  both what ships today and why `rude_clean_code` exports only `VERSION`.
- **Cutting a release?** See [Releasing to PyPI](guides/releasing.md) —
  the release workflow, trusted publishing, and the tag/version guard.
- **Changing code or workflows?** The [documentation standard](development/documentation.md)
  defines what "done" means for documentation impact.
- **Checking Python 3.11–3.13 compatibility?** See
  [Python version compatibility with tox](guides/python-version-compatibility.md)
  (auxiliary to the locked Pixi environment).

## Reference

- [Rules and configuration profiles](reference/rules.md) — implemented
  `CC001`–`CC601` rules, default options, and the Basic/Strict profiles.
- [Pixi and doit tasks](reference/pixi-tasks.md) — the locked task catalogue
  used by local development and CI.
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
and lychee for link validity. Vale (`pixi run --locked doit lint-prose`) and
alint (`pixi run --locked doit alint`) run in the `Policy` job. See
[running the checks](guides/running-the-checks.md) for details.

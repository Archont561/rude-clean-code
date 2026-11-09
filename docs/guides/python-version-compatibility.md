# Python version compatibility with tox

The environment of record for this repository is the locked Pixi
workspace (`pixi.toml` + `pixi.lock`), targeting Python >= 3.11 and
< 3.14 on linux-64. CI runs the locked checks on exactly that
configuration; everyday development needs nothing else.

Use [tox](https://tox.wiki/) to verify that the package works on every
Python version the project supports — for example, before a release, or
when you suspect version-specific behavior. tox runs the test suite in
isolated virtual environments, one per Python version. **tox ships in
the locked Pixi environment** as a PyPI dependency, so no separate
installation is needed, and it **runs in CI** as the `Python
compatibility` job in `.github/workflows/ci.yml`, a matrix over the
supported versions. The locked Pixi environment remains the environment
of record for development and release checks; tox is a complement to it,
not a replacement.

## Supported versions

The root `pyproject.toml` declares `requires-python = ">=3.11"`,
and the Pixi lock targets `>=3.11,<3.14`. The versions to test are
**3.11, 3.12 and 3.13** — the versions this repository supports today.
Do not test 3.9 or 3.10; the package does not support them.

## 1. Run tox through Pixi

tox is a locked PyPI dependency of the workspace, so:

```sh
pixi run --locked tox --version
```

Do not install tox into the Pixi environment with pip, and do not add it
to `[dependencies]` — `pixi add --pypi tox` already pinned it.

## 2. Configure tox

`tox.ini` is committed at the repository root — CI and local runs share
this one configuration. Its content is:

```ini
[tox]
envlist = py311, py312, py313
# The pyproject.toml at the repository root is the package manifest.
skip_missing_interpreters = false

[testenv]
description = Run the package BDD suite with pytest
# Without this, tox silently defaults to `package = skip` on trees with no
# recognizable build configuration: the suite runs but never installs the
# distribution and fails with PackageNotFoundError.
package = sdist
deps =
    pytest
    pytest-bdd
commands =
    pytest tests
```

The non-obvious setting is load-bearing:

- `package = sdist` — tox builds and installs the sdist into each
  environment, and the pytest-bdd suite then reads the installed
  distribution's metadata. Do not drop it: being implicit about the
  package configuration invites `PackageNotFoundError: No package
  metadata was found` and a long debugging session.

`.tox/` is gitignored so virtual environments never reach version
control. The `commands` mirror the `pixi run --locked doit test` task — the
package is built (hatchling) and installed into each tox environment,
and the pytest-bdd suite runs against the installed distribution,
reading `VERSION` from its metadata rather than from the source tree.

## 3. Run compatibility tests

```sh
pixi run --locked tox            # every environment in the envlist
pixi run --locked tox -e py313   # a single version
```

tox creates one virtualenv per entry under `.tox/`, installs the built
sdist and the listed dependencies there, and runs the commands.

## 4. Make Python interpreters available

tox does not install Python interpreters; it discovers them on `PATH`.
When tox runs inside `pixi run --locked`, the locked interpreter (3.13
as of writing) is on `PATH` and satisfies the matching `py313`
environment out of the box. The other environments need system
interpreters:

```sh
python3.11 --version
python3.12 --version
python3.13 --version
```

If a version is missing, install it through your operating system's
package manager or a version manager such as pyenv. A missing
interpreter is a hard error, not a warning: `skip_missing_interpreters`
is `false` in the committed configuration, so tox reports
`could not find python interpreter` and exits non-zero rather than
silently skipping a version you thought you tested. For a partial
sweep over only the versions you have, override on the command line,
for example `pixi run --locked tox -x testenv.skip_missing_interpreters=true`;
environments are then reported as `SKIP`, and tox still exits non-zero
if every requested environment was skipped.

## 5. CI/CD integration

The `Python compatibility` job in `.github/workflows/ci.yml` runs tox
on every push, pull request and manual dispatch, as a matrix over the
supported versions:

- one job per interpreter (`3.11`, `3.12`, `3.13`, quoted so unquoted
  `3.10`-style values cannot parse as numbers), kept in sync with the
  `tox.ini` `envlist`;
- `fail-fast: false`, so one failing version does not cancel the
  others;
- actions are pinned to commit SHAs with version comments, matching the
  rest of the workflow; `actions/setup-python` provides the interpreter
  for each matrix leg, and `prefix-dev/setup-pixi` provides the locked
  environment (and therefore tox itself);
- each leg runs `pixi run --locked tox -e <toxenv>` — the same
  configuration you use locally, not a re-implementation;
- `skip_missing_interpreters = false`, so a missing interpreter fails
  the job loudly instead of green-lighting a skipped leg.

Workflow changes are an ask-first action in this repository (see the
boundaries in `AGENTS.md`); the job landed on explicit maintainer
request.

Whether compatibility becomes a release gate is a separate decision and
is not wired in today. [tox-gh](https://github.com/tox-dev/tox-gh) maps
tox environments onto GitHub Actions runners directly and remains an
alternative to the explicit matrix.

## 6. Best practices

- Test what you support: 3.11, 3.12 and 3.13 today.
- Let tox manage isolated virtual environments; it never installs into the Pixi
  workspace itself (the locked 3.13 interpreter may seed the `py313`
  virtualenv).
- The Pixi workspace stays the environment of record for development and
  CI; tox is an auxiliary compatibility check.
- Test dependency bounds when dependencies are added (the package
  currently declares none): pin both the oldest and the newest
  supported versions and test against both.
- CI already fails loudly on missing interpreters (`skip_missing_interpreters = false`); keep it that way.

## Further reading

- [tox configuration reference](https://tox.wiki/en/4.47.2/reference/config.html)
- [OpenAstronomy packaging guide — tox](https://packaging-guide.openastronomy.org/en/latest/tox.html)
- [tox-gh — run tox environments on GitHub Actions](https://github.com/tox-dev/tox-gh)

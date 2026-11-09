# Python version compatibility with tox

The environment of record for this repository is the locked Pixi
workspace (`pixi.toml` + `pixi.lock`), targeting Python >= 3.11 and
< 3.14 on linux-64. CI runs the locked checks on exactly that
configuration; everyday development needs nothing else.

Use [tox](https://tox.wiki/) when you want to verify that the package
also works on the other Python versions the project supports — for
example, before a release, or when you suspect version-specific
behavior. tox runs the test suite in isolated virtual environments,
one per Python version. **tox ships in the locked Pixi environment**
as a PyPI dependency, so no separate installation is needed — but it is
**not wired into CI**; treat it as an auxiliary local tool.

## Supported versions

`packages/rude-clean-code/pyproject.toml` declares `requires-python = ">=3.11"`,
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

Create a `tox.ini` in the repository root:

```ini
[tox]
envlist = py311, py312, py313
package_root = packages/rude-clean-code
skip_missing_interpreters = true

[testenv]
description = Run the package BDD suite with pytest
package = sdist
deps =
    pytest
    pytest-bdd
commands =
    pytest packages/rude-clean-code/tests
```

Two non-obvious settings are required and both are load-bearing:

- `package_root = packages/rude-clean-code` — tox looks for the package
  to build in the *tox root* (where `tox.ini` lives). This repository
  has no root `pyproject.toml` by invariant, so you must point tox at
  the package directory explicitly.
- `package = sdist` — when tox finds no `pyproject.toml`, `setup.py` or
  `setup.cfg` in the tox root, it silently defaults to `package = skip`:
  the suite runs but never installs the distribution, and the BDD test
  fails with `PackageNotFoundError: No package metadata was found`.
  Be explicit, or you will be confused for a while (we were).

`tox.ini` and `.tox/` are gitignored on purpose: the locked Pixi
environment remains the source of truth for how this repository builds
and tests itself. The `commands` mirror the `pixi run --locked test`
task — the package is built (hatchling) and installed into each tox
environment, and the pytest-bdd suite runs against the installed
distribution, reading `VERSION` from its metadata rather than from the
source tree.

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
package manager or a version manager such as pyenv. The
`skip_missing_interpreters = true` setting lets tox skip missing
versions with a warning instead of failing; when you rely on the
result (for example, before a release), confirm every supported version
actually ran rather than silently skipping.

## 5. CI/CD integration

This repository's CI deliberately runs the locked Pixi environment on a
single Python version. Do not copy a tox matrix into
`.github/workflows/ci.yml` as an incidental change — workflow changes
are an ask-first action (see the boundaries in `AGENTS.md`).

For reference, a matrix job on its own repository would look like:

```yaml
name: Python compatibility

on: [push, pull_request]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - { python: "3.11", toxenv: py311 }
          - { python: "3.12", toxenv: py312 }
          - { python: "3.13", toxenv: py313 }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install tox
      - run: tox -e ${{ matrix.toxenv }}
```

Quote the versions (unquoted `3.10` parses as the number `3.1`), and
keep the `toxenv` names in sync with the `tox.ini` `envlist`.

Alternatively, [tox-gh](https://github.com/tox-dev/tox-gh) maps tox
environments onto GitHub Actions runners directly. If compatibility
testing should become a release gate for this repository, decide that
explicitly with the maintainer and wire it in as its own change.

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
- Automate in CI when it matters; make sure missing interpreters fail
  loudly instead of silently passing.

## Further reading

- [tox configuration reference](https://tox.wiki/en/4.47.2/reference/config.html)
- [OpenAstronomy packaging guide — tox](https://packaging-guide.openastronomy.org/en/latest/tox.html)
- [tox-gh — run tox environments on GitHub Actions](https://github.com/tox-dev/tox-gh)

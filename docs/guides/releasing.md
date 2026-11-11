# Releasing to PyPI and GitHub

The `rude-clean-code` package under `rude-clean-code/` is published to PyPI
and GitHub Releases by the
[release workflow](../../.github/workflows/release.yml), triggered by pushing a
version tag. PyPI publishing uses
[PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC):
no API token is stored in this repository or in GitHub secrets. The `pypi`
GitHub environment — configured in repository settings — holds the trust,
and the workflow's publish job requests its OIDC token.

## What the release workflow does

Three jobs, in order:

1. **Build and check distributions** (`build`): checks out the tag, sets up
   the locked Pixi environment, and runs the `build-release` task in
   [`automation/dodo.py`](../../automation/dodo.py). That task
   - verifies that the tag (sans a leading `v`) matches the `version` in
     `pyproject.toml` — a mismatch fails the job
     before anything can be uploaded;
   - deletes `dist/`, builds the sdist and wheel with `python -m build`
     (hatchling), and checks both with `twine check`;
   the distributions are then uploaded as the `distributions` workflow
   artifact.
2. **Publish to PyPI** (`publish`): downloads the `distributions` artifact
   and publishes it with `pypa/gh-action-pypi-publish`, without checking out
   the repository. This job grants no repository permission — only
   `id-token: write` for the OIDC exchange with PyPI — and runs in the
   `pypi` environment, so any protection rules configured there (for
   example, required reviewers) apply before anything is uploaded.
3. **Create GitHub Release** (`github-release`): runs after `build` and
   `publish` succeed. It checks out full repository history and tags,
   downloads the `distributions` artifact into `dist/`, and runs the
   `github-release` task in [`automation/dodo.py`](../../automation/dodo.py)
   (`github_release()` in
   [`automation/lib/packaging.py`](../../automation/lib/packaging.py)) with
   `permissions: contents: write`. That task re-verifies that the tag matches
   `pyproject.toml`, extracts the release notes for the tag via `convco`
   (falling back to `--generate-notes` when no visible sections exist), and
   publishes the GitHub Release via `gh release create --verify-tag` with both
   the wheel and sdist attached.

`build`, `twine`, and `convco` are part of the locked Pixi environment
(`pixi.toml`); nothing is pip-installed ad hoc.

## Cutting a release

1. Bump `version` in `rude-clean-code/pyproject.toml` (and refresh
   `CHANGELOG.md` with `convco` and the version badge in `README.md`), then
   commit and merge to `main`. Version bumps are a maintainer action.
2. Tag the commit with a `v`-prefixed tag matching the version, for
   example `git tag -a v0.2.0 -m "Release v0.2.0"`, and push the tag:
   `git push origin v0.2.0`.
3. The workflow builds, checks, publishes to PyPI, and creates the GitHub
   Release. PyPI rejects duplicate version numbers, so a version is published
   at most once; a failed release must be re-cut with a new version, never by
   re-tagging over a published one.

## Dry-running the build locally

```sh
pixi run --locked doit build-release
```

This performs the same build and `twine check`, writing distributions to
`dist/` (gitignored) without uploading anything. Outside CI it skips the
tag check, which only applies when `GITHUB_REF_NAME` (or `--ref`) is set.

## What is not automated

- **Tagging and version bumps are manual.** The workflow never creates
  tags and never edits the manifest.
- **The trusted publisher registration itself** lives on PyPI (project
  settings → publishing) and on GitHub (the `pypi` environment); changing
  it is a maintainer action outside this repository.

## CI coverage

Pull requests that change the workflow are covered by actionlint and by a
commit-message check (Policy job), and the workflow path is covered by
alint: `release.yml` must exist, and every `run:` step in `ci.yml` and
`release.yml` must be a single line — automation logic belongs in
[`automation/dodo.py`](../../automation/dodo.py) where it can be read and
tested, which is why the release logic itself lives in `build_release()` and
`github_release()` inside
[`automation/lib/packaging.py`](../../automation/lib/packaging.py).

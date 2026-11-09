# Releasing to PyPI

The package at the repository root is published to PyPI by the
[release workflow](../../.github/workflows/release.yml), triggered by pushing
a version tag. Publishing uses
[PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC):
no API token is stored in this repository or in GitHub secrets. The `pypi`
GitHub environment — configured in repository settings — holds the trust,
and the workflow's publish job requests its OIDC token.

## What the release workflow does

Two jobs, in order:

1. **Build and check distributions** (`build`): checks out the tag, sets up
   the locked Pixi environment, and runs
   [scripts/build-release.sh](../../scripts/build-release.sh). That script
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

`build` and `twine` are part of the locked Pixi environment
(`[pypi-dependencies]` in `pixi.toml`); nothing is pip-installed ad hoc.

## Cutting a release

1. Bump `version` in `pyproject.toml` and commit
   the change. Version bumps are a maintainer action.
2. Tag the commit with a `v`-prefixed tag matching the version, for
   example `git tag v0.1.0`, and push the tag: `git push origin v0.1.0`.
3. The workflow builds and publishes. PyPI rejects duplicate version
   numbers, so a version is published at most once; a failed release must
   be re-cut with a new version, never by re-tagging over a published one.

## Dry-running the build locally

```sh
pixi run --locked scripts/build-release.sh
```

This performs the same build and `twine check`, writing distributions to
`dist/` (gitignored) without uploading anything. Outside CI it skips the
tag check, which only applies when `GITHUB_REF_NAME` is set.

## What is not automated

- **Tagging and version bumps are manual.** The workflow never creates
  tags and never edits the manifest.
- **GitHub releases and changelogs** stay out of the release path; the
  changelog is generated from Conventional Commits with convco.
- **The trusted publisher registration itself** lives on PyPI (project
  settings → publishing) and on GitHub (the `pypi` environment); changing
  it is a maintainer action outside this repository.

## CI coverage

Pull requests that change the workflow are covered by actionlint and by a
commit-message check (Policy job), and the workflow path is covered by
alint: `release.yml` must exist, and every `run:` step in `ci.yml` and
`release.yml` must be a single line — shell logic belongs in `scripts/`
where it can be read and tested, which is why the build itself lives in
`scripts/build-release.sh`.

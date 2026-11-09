#!/bin/sh
# Build the release distributions for the package at the repository root and verify
# them with twine. Used by .github/workflows/release.yml (runs inside the
# locked Pixi environment, so `python -m build` and `twine` are available).
# Also runnable locally: pixi run --locked scripts/build-release.sh
#
# When GITHUB_REF_NAME holds a git tag (CI), the tag (sans a leading 'v')
# must match the package version — a mismatch fails before any upload can
# happen, because the publish job only runs if this script succeeds.
set -eu
cd "$(git rev-parse --show-toplevel)"

if [ -n "${GITHUB_REF_NAME:-}" ]; then
  tag="${GITHUB_REF_NAME#v}"
  package_version="$(python - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as fh:
    print(tomllib.load(fh)["project"]["version"])
PY
)"
  if [ "${tag}" != "${package_version}" ]; then
    echo "Tag '${GITHUB_REF_NAME}' does not match package version '${package_version}'." >&2
    exit 1
  fi
fi

# Start from a clean tree so stale artifacts never leak into an upload.
rm -rf dist
python -m build --outdir dist .
twine check dist/*

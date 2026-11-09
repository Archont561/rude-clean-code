#!/bin/sh
# Check that every incoming commit message is conventional.
# Used by the Policy job in .github/workflows/ci.yml (runs inside the
# locked Pixi environment, so `convco` is on PATH). Also runnable locally:
#   COMMIT_BASE=<sha> COMMIT_HEAD=<sha> pixi run --locked scripts/check-commit-messages.sh
#
# A zero or unresolvable event base (first push, branch creation) must not
# fail the job: derive a base from the repository, and skip cleanly when no
# valid range can be formed.
set -eu
head="${COMMIT_HEAD:-}"
base="${COMMIT_BASE:-}"
zero="0000000000000000000000000000000000000000"
if [ -z "${base}" ] || [ "${base}" = "${zero}" ]; then
  if git cat-file -e 'HEAD^' 2>/dev/null; then
    base="$(git rev-parse HEAD^)"
  else
    base="$(git rev-list --max-parents=0 HEAD | head -n 1)"
  fi
fi
if [ -z "${head}" ] || ! git cat-file -e "${head}^{commit}" 2>/dev/null; then
  echo "No valid head ('${head:-empty}'); skipping commit-message check."
  exit 0
fi
if [ -z "${base}" ] || ! git cat-file -e "${base}^{commit}" 2>/dev/null; then
  echo "No valid base ref available (event base: '${COMMIT_BASE:-empty}'); skipping commit-message check."
  exit 0
fi
echo "Checking commits ${base}..${head}"
convco check "${base}..${head}"

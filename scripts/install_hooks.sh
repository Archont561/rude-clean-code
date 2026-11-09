#!/bin/sh
# Install only when Lefthook reports missing or stale hooks.
set -eu

if lefthook check-install; then
  echo 'Lefthook hooks are already installed.'
else
  status=$?
  if [ "$status" -ne 1 ]; then
    echo "Unable to check Lefthook hooks (exit $status)." >&2
    exit "$status"
  fi
  lefthook install
  lefthook check-install
  echo 'Lefthook hooks installed.'
fi

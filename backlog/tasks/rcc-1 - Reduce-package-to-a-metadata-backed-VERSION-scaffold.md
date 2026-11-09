---
id: RCC-1
title: Reduce package to a metadata-backed VERSION scaffold
status: Done
assignee: []
created_date: '2026-11-08 18:30'
updated_date: '2026-11-08 18:30'
labels: []
dependencies: []
priority: high
type: task
ordinal: 1000
milestone: m-0
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Restructure the repository into the Archont561 monorepo layout and leave
the single distribution with only a VERSION initializer and a
package-local BDD version test. pyproject.toml is the version source of
truth; no lint rules are implemented yet (decision-4).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The distribution lives at packages/rude-clean-code/ with its own pyproject.toml, README and LICENSE, and its source tree contains only __init__.py, with VERSION as the sole public export derived from installed metadata built from pyproject.toml.
- [x] #2 The package has only a package-local version BDD feature and test (features/package_version.feature, tests/test_package_version_bdd.py) checking VERSION against pyproject.toml, installed metadata, the mocked metadata lookup, and the minimal source layout.
- [x] #3 The root is a Pixi workspace (pixi.toml, ruff.toml, scripts/, lefthook.yml, .versionrc) with backlog config, decisions, a specification doc, a milestone and tasks defined; no root pyproject.toml, root src/, root tests/ or root docs/ remain.
- [x] #4 The built wheel installs into a clean environment and the package-local BDD test passes against it.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Delete DEVELOPMENT.md and the flat rule implementation; move the
distribution under packages/; write the VERSION initializer, feature and
BDD test in the artifactspec package-version pattern; define backlog
records; adapt Pixi tasks, scripts/check_packages.py, lefthook and CI to
package-local paths; build, install into a clean venv and run the suite.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Recorded at completion of RCC-1; verification results are reported with
the change. GitHub CI remains unverified until pushed.
<!-- SECTION:FINAL_SUMMARY:END -->

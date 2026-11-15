---
id: RCC-8
title: Implement project-wide rules when Rude permits
status: To Do
assignee: []
created_date: 2026-11-08 19:05
updated_date: '2026-11-15T16:26:00Z'
labels: []
milestone: m-5
dependencies:
  - RCC-2
documentation:
  - >-
    backlog/docs/doc-1 -
    Rude-Clean-Code-product-and-architecture-specification.md
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: feature
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement CC203 (inheritance depth), CC502 (cross-file duplication),
and CC703 (circular dependencies) from doc-2. This task is blocked on
capability, not effort: Rude 0.1a4 gives rules a per-file context with
no project-level lifecycle hook, so these detections cannot be honest
`Rule`s yet. The codes stay reserved and unimplemented rather than
being faked with per-file approximations or process-global caches.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The task starts with a recorded assessment: either the installed Rude exposes a project-level provider or lifecycle hook sufficient for an order-independent, parallel-safe index, or a new backlog decision approves a separate indexer distribution (decision-1). Without one of these, the task stops and reports the blocker instead of shipping an approximation.
- [ ] #2 Detections are order-independent and give identical results under parallel checking (`--jobs` greater than 1) and single-process checking, proven by tests running the same fixture project both ways.
- [ ] #3 Each rule has fixture-project tests (multi-file packages with known cycles, duplications, and inheritance chains), including acyclic and non-duplicated projects reporting nothing.
- [ ] #4 Until this task lands, no release notes, README, or rule documentation claims CC203, CC502, or CC703 as available.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Re-check the installed Rude release for project-level providers; record the assessment in the task notes and, if needed, draft the indexer-distribution decision for user approval.
2. Build the project index (module graph, inheritance graph, normalised subtree hashes) behind whichever mechanism step 1 approved.
3. Implement the three rules on the index with multi-file fixtures, verify parallel and single-process equivalence, and run `pixi run ci`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Blocker re-verification — 2026-11-15

Re-checked upstream before starting work, as acceptance criterion #1 requires. The blocker is unchanged.

**PyPI** (`https://pypi.org/pypi/rude/json`): `info.version` is still `0.1a4`. All published releases are `0.1a1` (2025-01-31), `0.1a2` (2026-05-20), `0.1a3` (2026-05-21), `0.1a4` (2026-06-05). Nothing newer exists.

**Upstream repository** (`github.com/rude-dev/rude`, discovered from the PyPI `project_urls`; note that `Archont561/rude` does not exist and is not the upstream):

- `main` is **0 commits ahead** of tag `v0.1a4` (verified with the GitHub compare API). No unreleased provider work is sitting on the default branch.
- Tags stop at `v0.1a4`.
- Branches are dependency-update bumps and two chore branches; none target a project provider.
- Open issues are dependency bumps plus one UI request (#33, summary-line stats). No project-level provider issue is open.
- Last push to `main`: 2026-08-30, and that push is contained in `v0.1a4`.

**Installed API surface** (`rude 0.1a4`):

- `rude.providers` exposes exactly `ParentProvider`, `QualifiedNameProvider`, `ScopeProvider` — all per-file. No project, index, or workspace provider.
- `Rule` exposes `check`, `configure`, `diagnostic`, `diagnostic_at`, `should_check_file` — no project-level lifecycle hook (no `setup`, `finalize`, or index callback).
- `FileContext` exposes only per-file members (`lines`, `text`, `path`-scoped helpers, `get_metadata`/`set_metadata`); nothing reaches across files.

**Conclusion:** `CC203` (inheritance depth), `CC502` (cross-file duplication), and `CC703` (circular dependencies) still cannot be honest `Rule`s, exactly as this task describes. Carrying on would mean faking them with process-global caches, which doc-1 section 5 and this task both prohibit because results would depend on file order and break under parallel checking.

The task stays blocked. Re-check stands at: PyPI version newer than `0.1a4`, or a provider/lifecycle addition in `rude-dev/rude`.
<!-- SECTION:NOTES:END -->

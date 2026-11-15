---
id: RCC-15
title: Assess a broader Feature Envy detector after CC606 ships
status: Done
assignee:
  - '@agent'
created_date: '2026-11-15T13:53:00Z'
updated_date: '2026-11-15T16:09:00Z'
labels: []
milestone: m-6
dependencies:
  - RCC-13
references:
  - https://github.com/Archont561/rude-clean-code/issues/27
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: spike
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CC606 as scoped covers one narrow, honest shape: two parameters of the same annotated type read for their attributes. Issue #27 points at the wider smell the clean-code skill names (`doc-*`, `.agents/skills/refactor`) in which a method uses another object's data more than its own, and that shape appears in this repository too: every rule visitor touches far more of the node it inspects than of `self`. The narrow rule deliberately does not attempt it.

The wider detector needs evidence before code exists. A per-file heuristic that fires on every visitor in this very plugin would be unusable, and a threshold tuned until this repository looks clean would be dishonest. The spike measures the shape on real code, decides whether a per-file proxy is trustworthy at all, and records the answer so a future task either implements it with a measured budget or declines it with a reason. No rule code ships from this task.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The assessment records, for at least five real repositories including this one, how often a method or function reads more foreign attributes than locals or `self` attributes, and what share of those hits are conventional idioms (visitors, serializers, comparators, adapters, test helpers).
- [x] #2 The note states a recommendation with evidence: implement a per-file heuristic with named thresholds, or decline it as out of reach for a per-file analyzer, and either way names the rule code that would carry it (or why the code stays unallocated).
- [x] #3 If the recommendation is to implement, a follow-up backlog task is created under m-6 with acceptance criteria in the same shape as RCC-13; if it is to decline, doc-2 records the decision next to the CC6xx family so the gap is documented rather than rediscovered.
- [x] #4 `backlog/docs/doc-1 - Rude-Clean-Code-product-and-architecture-specification.md` and doc-2 describe the CC6xx family consistently after the assessment, with no rule claimed as shipped before it exists.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Build a throwaway measurement script (not shipped) that parses each repository with Rude's own tree-sitter API and, per function, counts attribute reads whose receiver resolves to a parameter ("foreign") versus reads rooted at `self`/`cls` ("own").
2. Run it across the same five-repository corpus RCC-11 and RCC-13 used, plus this repository itself, and record totals per repository.
3. Classify a sample of the hits by idiom (visitor/dispatch, serializer/comparator, adapter/facade, test helper, genuine envy) to get the false-positive-relevant share.
4. Test whether any threshold separates genuine envy from conventional idiom without tuning on this repository.
5. Decide: implement with named thresholds, or decline with a recorded reason. Record the evidence in the task notes and write the decision into doc-2 next to the CC6xx family.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Assessment: a broader per-file Feature Envy detector

Measured on 2026-11-15 with a throwaway harness (Rude tree-sitter parse, per function: attribute reads whose receiver root is a parameter or a local derived from one, versus reads rooted at `self`/`cls`). Same five-repository corpus RCC-11 and RCC-13 used: 300 files, 90,434 LOC, 3,493 functions that read any attribute.

#### Baseline: the naive signal fires everywhere

A function reading more foreign than own state:

| Repository | Functions | Foreign majority | Share |
| --- | --- | --- | --- |
| `this_repo_src` | 317 | 157 | 49.53% |
| `rude` | 387 | 128 | 33.07% |
| `packaging` | 305 | 85 | 27.87% |
| `tox` | 946 | 271 | 28.65% |
| `_pytest` | 1,538 | 455 | 29.58% |
| **Total** | **3,493** | **1,096** | **31.4%** |

31% of all functions would fire. That is not a lint rule, it is a property of the language.

#### Narrowing 1: exclude static and class methods

45.2% of the method candidates carried the static or class method decorator, where there is no genuine `self` to be envious of. Requiring a real `self` and at least one own read drops the share to 4.95% (173 functions).

#### Narrowing 2: exclude visitor and protocol hooks

Of those 173, 37.6% are named like hooks (`check`, `visit`, `handle`, `render`, `serialize`, `__call__`) or take a recognised node/context parameter. A further large share are pure functions written as methods — `_is_url_line(self, line: str)` reads no `self` state at all and is a plain function wearing a method signature.

The decisive measurement: **all 13 candidates in this repository are `Rule.check(node)` methods**, the plugin's own extension point. This plugin alone has 60 of them.

#### Narrowing 3: the "does a type exist to move onto?" test

Of the 173 remaining candidates, the parameter annotations resolve as:

| Annotation | Count | Share |
| --- | --- | --- |
| Type not defined in the file (imported, elsewhere) | 132 | 76.3% |
| Type defined in the same file | 13 | 7.5% |
| Builtin only | 4 | 2.3% |
| No usable annotation | 24 | 13.9% |

76.3% would have no local type to move the behaviour onto, and per-file analysis cannot verify that the remote type is even a project type rather than a third-party or stdlib class. Suggesting "move this onto `Node`" is not actionable advice when `Node` belongs to Rude.

#### Recommendation: decline

The honest options and why each fails:

- **Ship it at `INFO` with the visitor exemptions.** The rule would still need a hook-name allowlist and a node-parameter allowlist to reach a tolerable rate. That is a name-based heuristic with a hand-maintained exempt list in every consumer — the kind of rule this project has rejected elsewhere (`CC602`/`CC603` stay silent rather than guess). And the residual hits are dominated by pure functions written as methods, which is a style preference, not envy.
- **Restrict to the "envious method" shape (real `self`, some own reads, imported-type parameter).** 132 candidates across 90k LOC, dominated by adapter and serializer methods where borrowing is the job. Without cross-file type identity there is no way to distinguish a serializer from an envious helper.
- **Require the parameter type to be defined in the same file.** That collapses to 13 hits (7.5%), all of which are already style-adjacent to what `CC606` and `CC605` catch, and it contradicts the original motivation in issue #27, where the type was imported.

**Decision: no rule ships from this spike, and no code is allocated.** Per-file analysis cannot separate genuine Feature Envy from the visitor, adapter, serializer, and static-helper idioms that dominate real code, and the one signal that does survive (a method borrowing more than it owns) fires on 5% of functions with an actionable-advice rate well under half. Shipping it would cost consumers more suppression comments than it saves refactors, which is the same reason `CC203`, `CC502`, and `CC703` are deferred rather than approximated.

CC606 remains the honest subset of this idea: it requires two same-type parameters and an attribute-read threshold, so it fires 0.07 times per 1k LOC instead of 12 times.

Revisit only if Rude exposes a project-level provider that can resolve cross-file type identity, in which case the "does a comparable type exist and does it already own this behaviour" question becomes answerable.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Assessed a broader per-file Feature Envy detector and declined it with measurements. Across 3,493 functions in 300 files / 90,434 LOC, 31.4% read more foreign than own state; excluding static and class methods drops that to 4.95%, and of those 37.6% are visitor or protocol hooks while the rest are dominated by pure functions written as methods. All 13 candidates in this repository are `Rule.check(node)` methods, the plugin's own extension point, and 76.3% of the narrowed candidates have no in-file type to move behaviour onto. No rule code ships and no code is allocated; the decision is recorded in doc-2 next to the CC6xx family and cross-referenced from doc-1. CC606 remains the honest subset of the smell.
<!-- SECTION:FINAL_SUMMARY:END -->

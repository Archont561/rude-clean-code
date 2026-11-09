---
id: doc-1
title: Rude Clean Code product and architecture specification
type: specification
created_date: 2026-11-08 18:30
updated_date: '2026-11-09T23:06:00Z'
tags:
  - specification
  - architecture
  - product
---
## Status and purpose

**Design specification, not an implementation claim.** This document
captures the agreed direction for a Clean Code / SOLID-inspired plugin
for the Rude Python linter. The package is currently a version-only
scaffold (decision-4): no rule in this document exists as code yet.
"Must" describes the intended product contract. Historical decisions are
recorded in `backlog/decisions/`.

## 1. Product vision

`rude-clean-code` is a reusable, opinionated Python engineering-standard
plugin, installable into any Python repository next to Rude and
discovered through Rude's `rude.plugins` entry point (decision-1). It
translates Clean Code principles into explicit, documented, testable
rules wherever static analysis permits. It is an engineering standard
implemented on Rude's extension API; installing it does not mean Rude
itself guarantees SOLID compliance.

## 2. Rule catalogue (planned)

Codes follow decision-5 (`CC` + family digit + two digits). Severity
follows the classification in §4. This table is the summary; the full
proposed catalogue with per-rule detection contracts, configuration
options, scope limits, and false-positive notes is **doc-2 (Proposed
rule catalogue and detection contracts)** and includes families and rules
only summarised here (`CC0xx` module and package organization, `CC105`–`CC108`
parameter and dead-helper checks, `CC204`–`CC207` class coupling and base
counts, `CC304`–`CC311` readability and fail-fast rules, `CC4xx` naming
details, `CC5xx` DRY variants, `CC6xx` SOLID and Demeter indicators,
`CC8xx` design-pattern boundaries, and `CC9xx` comment, suppression, and
docstring accuracy rules).

| Code | Rule | Detection |
| --- | --- | --- |
| CC001–CC005 | Module organization, `__init__.py` facades, and `__all__` | Line count, AST top-level exports, relative imports |
| CC101 | Function too long | Line count |
| CC102 | Too many parameters | Signature |
| CC103 | Too many return statements | AST, own scope |
| CC104 | Too many local variables | Scope analysis |
| CC201 | Class too large | Line count |
| CC202 | Too many methods | Class body |
| CC203 | Excessive inheritance depth | Inheritance graph (project-wide, §5) |
| CC301 | Excessive nesting | AST depth, own scope |
| CC302 | Excessive boolean operands | Boolean expression analysis |
| CC303 | Excessive branching | Branch count (distinct from Rude's C901) |
| CC306–CC311 | Readability, `global` state, and fail-fast error handling | AST expressions, `except`/`raise`/`try` structure |
| CC401 | Unclear naming | Naming heuristics |
| CC501 | Duplicate function bodies | AST similarity (same file first, §5) |
| CC502 | Duplicate code blocks | Subtree similarity (project-wide, §5) |
| CC601 | Repeated type-switch dispatch | `isinstance`/conditional analysis |
| CC602 | Suspicious overridden methods (LSP indicators) | Inheritance analysis |
| CC604–CC605 | Law of Demeter and private member access | Attribute/call chains and `_attr` receivers |
| CC701 | Forbidden concrete imports in domain code | Config-driven import analysis |
| CC801–CC805 | Design-pattern boundaries (repository, factory, strategy, decorator, DI) | Config-driven; see doc-2 |
| CC901–CC910 | Documentation, `TODO` markers, suppressions, and comment accuracy | AST, docstring sections, and comment analysis; see doc-2 |

Every diagnostic message must carry the measured value, the configured
limit, and a suggested action; the long "why" lives in the rule docstring
and this catalogue. Rude diagnostics have no structured explanation
fields, so nothing more may be promised.

## 3. Configuration and profiles (planned)

Per-rule options come from `[tool.rude.rules.<CODE>]` via each rule's
`configure()` method. Rude 0.1a4 has no profile or preset mechanism and
no `--strict` flag, so profiles are versioned TOML snippets consumers
copy into their `pyproject.toml`:

- **Basic**: CC1xx–CC3xx size and complexity limits.
- **Strict**: Basic + CC401, CC501, CC601.
- **Architecture**: Strict + CC701 with consumer-named forbidden modules
  and domain paths (a generic plugin cannot know a consumer's layering,
  so CC701 is inert until configured).

## 4. Deterministic vs heuristic

| Type | Example | Default severity |
| --- | --- | --- |
| Deterministic | Function exceeds 30 lines | WARNING |
| Structural | Class has excessive coupling proxies | WARNING |
| Heuristic | Class likely violates SRP | INFO |
| Semantic | Subclass potentially violates LSP | INFO |

Only `Severity.ERROR` fails CI in Rude, and no CC rule defaults to it
(decision-5). Counts are conversation starters, not proof: cohesion and
relationship analysis must be labelled heuristic when it arrives.

## 5. Scope limits of Rude 0.1a4

Rude rules receive a per-file `FileContext`; its providers
(`ParentProvider`, `ScopeProvider`, `QualifiedNameProvider`) are per
file, and there is no project-level lifecycle hook. Cross-file
duplication, circular dependencies, true inheritance depth and coupling
graphs therefore cannot be honest `Rule`s yet. They are deferred until
Rude exposes a project provider, or delivered as a separate indexer
distribution under a new decision (decision-1). Faking them with
process-global caches is prohibited: results would depend on file order
and break under parallel checking.

Autofixes are limited to Rude's node-level `Fix` operations and ship
only where the transformation is provably semantics-preserving; no
extraction-style fix qualifies.

## 6. Phasing

1. Deterministic core: CC101–CC104, CC201–CC202, CC301–CC303.
2. In-file heuristics, module organization, and fail-fast extensions:
   CC001–CC005, CC107, CC207, CC306, CC308–CC311, CC401–CC403, CC501
   (same file), CC601.
3. Config-driven architecture: CC701–CC702, CC704, then the CC8xx
   design-pattern boundary rules (doc-2); profiles published as snippets.
4. Maturing heuristics and documentation/comment rules: CC105–CC106,
   CC108, CC204–CC206, CC304–CC305, CC307, CC503–CC504, CC602–CC605,
   CC901–CC910.
5. Project-wide analysis when Rude permits it (§5): CC203, CC502,
   CC703, circular dependencies.
6. Safe autofixes only, per §5.

Per-rule implementation order and acceptance detail: doc-2,
"Implementation order".

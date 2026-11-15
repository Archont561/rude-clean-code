---
id: RCC-14
title: Add opt-in flagged_dunders escalation to CC605
status: To Do
assignee: []
created_date: '2026-11-15T13:53:00Z'
labels: []
milestone: m-6
dependencies:
  - RCC-11
references:
  - https://github.com/Archont561/rude-clean-code/issues/27
documentation:
  - backlog/docs/doc-2 - Proposed-rule-catalogue-and-detection-contracts.md
priority: low
type: enhancement
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CC605 skips every dunder member, and that default is right: `obj.__name__`, `obj.__doc__`, and `obj.__class__` are ordinary protocol surface, not encapsulated internals. The default also hides the one real signal the issue reports. Reaching for `fn.__code__.co_filename` or `obj.__closure__` crosses a module boundary and reaches into implementation internals that the owning type never promised to keep, yet nothing in the plugin reports it.

Rather than widen CC605 and flood every consumer that reads `__name__`, the rule gets an opt-in list. Empty by default means behaviour is unchanged for every existing consumer of 0.3.1, and a consumer who wants the escalation names the dunders that matter in their project. Issue #27 proposes exactly this shape (`flagged_dunders` with `__code__`, `__closure__`, `__globals__`, `__dict__`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 CC605 accepts a `flagged_dunders` option validated through `parse_str_list_option`; an empty list (the default) keeps the current behaviour exactly, so no existing configuration starts reporting new diagnostics.
- [ ] #2 When a consumer names a dunder, the rule reports that member on receivers other than `self`, `cls`, and `super()`, at INFO, with the same indicator wording as the single-underscore path, and `allowed_members` keeps winning over `flagged_dunders`.
- [ ] #3 Package-local tests prove the empty default reports nothing for `__name__`, `__doc__`, `__class__`, and `__code__`; a configured `flagged_dunders` reports the name on an external receiver; and `self.__dict__` together with `allowed_members` remain exempt.
- [ ] #4 An invalid value (a non-list, or a list holding a non-string) raises the standard `CC605 option ...` `ValueError` from `_scope.py`, covered by a test.
- [ ] #5 `docs/reference/rules.md` documents the new option in the CC605 row with its empty default, and doc-2 records the escalation alongside the existing CC605 contract.
<!-- AC:END -->

---
id: RCC-14
title: Add opt-in flagged_dunders escalation to CC605
status: Done
assignee:
  - '@agent'
created_date: '2026-11-15T13:53:00Z'
updated_date: '2026-11-15T14:14:00Z'
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
- [x] #1 CC605 accepts a `flagged_dunders` option validated through `parse_str_list_option`; an empty list (the default) keeps the current behaviour exactly, so no existing configuration starts reporting new diagnostics.
- [x] #2 When a consumer names a dunder, the rule reports that member on receivers other than `self`, `cls`, and `super()`, at INFO, with the same indicator wording as the single-underscore path, and `allowed_members` keeps winning over `flagged_dunders`.
- [x] #3 Package-local tests prove the empty default reports nothing for `__name__`, `__doc__`, `__class__`, and `__code__`; a configured `flagged_dunders` reports the name on an external receiver; and `self.__dict__` together with `allowed_members` remain exempt.
- [x] #4 An invalid value (a non-list, or a list holding a non-string) raises the standard `CC605 option ...` `ValueError` from `_scope.py`, covered by a test.
- [x] #5 `docs/reference/rules.md` documents the new option in the CC605 row with its empty default, and doc-2 records the escalation alongside the existing CC605 contract.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Implementation Notes (CC605 flagged_dunders)

Added `flagged_dunders` to `ExternalPrivateAccess` in `rude-clean-code/src/rude_clean_code/rules/coupling_heuristics.py`, validated through `parse_str_list_option` like every other list option. The default is an empty tuple, so every consumer on 0.3.1 sees byte-identical behaviour: dunders stay exempt until named.

The guard was reordered so `allowed_members` wins before the dunder check runs, then the escalation is computed once:

```python
if name in self.allowed_members:
    return
escalated = is_dunder(name) and name in self.flagged_dunders
if not escalated and (
    not name.startswith("_") or name == "_" or is_dunder(name)
):
    return
```

`self`/`cls`/`super()` receivers stay exempt on the escalated path too, because the receiver check follows the name checks unchanged. Coverage: `test_cc605_flagged_dunders_escalation`, `test_cc605_flagged_dunders_respects_receiver_and_allowed_members` (which also pins the empty-default silence for `__name__`, `__doc__`, `__class__`, and `__code__`), plus the option-validation case in `test_rcc11_invalid_options_raise_value_error`, and a BDD scenario in `feature_envy.feature`.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the opt-in `flagged_dunders` option to CC605 with an empty default, so escalation to implementation internals such as `__code__` is a consumer decision and no 0.3.1 configuration starts reporting new diagnostics. Covered by unit tests for escalation, receiver and `allowed_members` precedence, empty-default silence, and option validation, plus a BDD scenario. Documented in `docs/reference/rules.md` and doc-2.
<!-- SECTION:FINAL_SUMMARY:END -->

---
id: m-1
title: "02 - Deterministic core rules"
---

## Description

Outcome: `rude-clean-code` stops being a version-only scaffold and becomes an installable Rude plugin whose nine deterministic rules (CC101-CC104, CC201-CC202, CC301-CC303) are discovered through the `rude.plugins` entry point, selected by `CC`/`CC1`-style prefixes, and trusted because every threshold is unit- and property-tested. Scope is the plugin machinery (entry point, RULES registry, own-scope traversal, per-rule configuration) plus those rules; no heuristics, no config-driven architecture rules. Target one session and one PR; assess release readiness after verification.

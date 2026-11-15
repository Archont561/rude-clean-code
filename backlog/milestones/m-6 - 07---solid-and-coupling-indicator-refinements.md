---
id: m-6
title: "07 - SOLID and coupling indicator refinements"
---

## Description

Outcome: the CC6xx indicator family closes the gaps found in real consumer code after v0.3.1. Issue #27 records an external helper comparing one type's private and public attributes that no shipped rule flagged: CC604 stays silent at the default depth and CC605 deliberately skips dunders. This milestone adds the Feature Envy indicator CC606 and the opt-in CC605 dunder escalation, each as an INFO indicator with a measured false-positive budget, package-local tests, and catalogue entries in doc-2.

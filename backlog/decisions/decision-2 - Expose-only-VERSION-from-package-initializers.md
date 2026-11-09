---
id: decision-2
title: Expose only VERSION from package initializers
date: '2026-11-08'
status: accepted
---

## Context

The package root should remain minimal and have a predictable version
constant.

## Decision

The package initializer explicitly exports only the `VERSION` constant via
`__all__`. `VERSION` is read with `importlib.metadata.version()` from the
installed distribution metadata, which Hatchling builds by parsing this
package's `pyproject.toml`; `pyproject.toml` is therefore the version
source of truth and no version string is duplicated in source. The package
has a local BDD test checking the fresh root namespace and that `VERSION`
matches `pyproject.toml` and its installed distribution version.

## Consequences

Public functionality will live in submodules; importing `rude_clean_code`
never imports Rude or executes plugin code. Because `VERSION` needs
installed metadata, an uninstalled source tree cannot be imported, so
Pixi test tasks must install the local package first (`install-projects`).
Python can add submodule attributes to a package namespace after
submodules are imported, which is why the BDD check inspects a fresh
interpreter.

# Rude Clean Code scaffold

`rude-clean-code` is a placeholder for a future Clean Code / SOLID-inspired
plugin for the Rude Python linter. It currently exposes only `VERSION`, read
from installed distribution metadata. It does not depend on Rude and does not
implement any lint rules yet; the planned rule catalogue and severity
contract live in the repository backlog specification
(`backlog/docs/doc-1 - Rude-Clean-Code-product-and-architecture-specification.md`).

After installing the local project, inspect the version with:

```python
from rude_clean_code import VERSION

print(VERSION)
```

The version is declared in this package's `pyproject.toml`, which is the
version source of truth: Hatchling parses it at build time and writes it
into the installed distribution metadata that `VERSION` reads back. The
repository's `pixi run --locked test` task installs the local package and
runs this package's BDD tests against the current source. Reinstall after
changing package metadata. See the [repository](https://github.com/Archont561/rude-clean-code)
for the design, contribution guide, and current status.

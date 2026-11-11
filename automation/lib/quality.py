"""Quality, linting, and Rude dogfooding helpers for repository automation."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = "rude-clean-code"
DOGFOOD_TARGETS = (PACKAGE_DIR, "automation")

VALE_TARGETS = (
    "README.md",
    "rude-clean-code/README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "backlog",
    "docs",
)

MARKDOWN_TARGETS = (
    "README.md",
    "rude-clean-code/README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "docs/**/*.md",
)


def workflow_files(root: Path = ROOT) -> list[str]:
    """Return sorted relative paths of GitHub Actions workflow files."""
    workflows_dir = root / ".github" / "workflows"
    return sorted(str(path.relative_to(root)) for path in workflows_dir.glob("*.yml"))


def parse_rude_diagnostics(stdout: str) -> list[dict[str, Any]]:
    """Parse newline-delimited JSON diagnostics emitted by Rude."""
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def dogfood_rude(
    root: Path = ROOT,
    paths: Sequence[str] | None = None,
) -> None:
    """Run Rude with this repository's dogfood CC profile and fail on any diagnostic."""
    resolved = tuple(paths) if paths is not None else DOGFOOD_TARGETS
    cmd = [
        sys.executable,
        "-m",
        "rude",
        "check",
        "--config",
        str(root / PACKAGE_DIR / "pyproject.toml"),
        "--format",
        "json",
        *resolved,
    ]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
    diagnostics = parse_rude_diagnostics(result.stdout)
    if diagnostics:
        details = "\n".join(
            f"{d['file']}:{d['line']}:{d['column']}: {d['code']} {d['message']}"
            for d in diagnostics
        )
        raise RuntimeError(f"Rude dogfood checks failed:\n{details}")
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or f"Rude failed with exit {result.returncode}"
        )
    print("Rude dogfood check passed (0 diagnostics).")

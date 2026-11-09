"""Unified repository task automation for Rude Clean Code (executed via doit)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ZERO_SHA = "0" * 40

VALE_TARGETS = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "backlog",
    "docs",
)

MARKDOWN_TARGETS = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "docs/**/*.md",
)

DOIT_CONFIG: dict[str, Any] = {
    "default_tasks": ["ci"],
    "verbosity": 2,
    "backend": "sqlite3",
    "dep_file": ".doit.db",
}


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def _run_isolated(args: Sequence[str], *, cwd: Path = ROOT) -> None:
    subprocess.run(list(args), cwd=cwd, env=_clean_env(), check=True)


def _git_is_commit(root: Path, ref: str) -> bool:
    if not ref:
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}^{{commit}}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _workflow_files(root: Path = ROOT) -> list[str]:
    workflows_dir = root / ".github" / "workflows"
    return sorted(str(path.relative_to(root)) for path in workflows_dir.glob("*.yml"))


def clean_coverage(root: Path = ROOT) -> None:
    """Remove generated coverage report artifacts."""
    (root / "coverage.xml").unlink(missing_ok=True)
    (root / ".coverage").unlink(missing_ok=True)


def clean_distributions(root: Path = ROOT) -> None:
    """Remove local distribution check artifacts."""
    shutil.rmtree(root / "distributions", ignore_errors=True)


def clean_dist(root: Path = ROOT) -> None:
    """Remove release distribution artifacts."""
    shutil.rmtree(root / "dist", ignore_errors=True)


def check_packages(
    root: Path = ROOT,
    sources: Sequence[Path] | None = None,
) -> None:
    """Build wheel and sdist into distributions/, run twine check, and inspect wheels."""
    package_sources = tuple(sources) if sources is not None else (root,)
    outputs = root / "distributions"
    shutil.rmtree(outputs, ignore_errors=True)
    outputs.mkdir(parents=True, exist_ok=True)
    for source in package_sources:
        _run_isolated(
            [
                sys.executable,
                "-m",
                "build",
                str(source),
                "--outdir",
                str(outputs),
            ],
            cwd=root,
        )
    files = sorted(outputs.iterdir())
    if len(files) != 2 * len(package_sources):
        raise RuntimeError("Expected one wheel and one sdist per distribution")
    _run_isolated(
        [sys.executable, "-m", "twine", "check", *(str(path) for path in files)],
        cwd=root,
    )
    for wheel in sorted(outputs.glob("*.whl")):
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
                raise RuntimeError(f"License missing from {wheel.name}")
            if "rude_clean_code/__init__.py" not in names:
                raise RuntimeError(f"Package initializer missing from {wheel.name}")


def build_release(ref_name: str = "", root: Path = ROOT) -> None:
    """Verify an optional release tag matches pyproject.toml, build dist/, and run twine check."""
    if ref_name:
        tag = ref_name.removeprefix("v")
        manifest = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        package_version = manifest["project"]["version"]
        if tag != package_version:
            raise RuntimeError(
                f"Tag '{ref_name}' does not match package version '{package_version}'."
            )
    dist_dir = root / "dist"
    shutil.rmtree(dist_dir, ignore_errors=True)
    _run_isolated(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir), str(root)],
        cwd=root,
    )
    files = sorted(dist_dir.iterdir())
    if len(files) != 2:
        raise RuntimeError(
            f"Expected one wheel and one sdist in {dist_dir}, found {len(files)}."
        )
    _run_isolated(
        [sys.executable, "-m", "twine", "check", *(str(path) for path in files)],
        cwd=root,
    )


def install_hooks(root: Path = ROOT) -> None:
    """Install or verify Lefthook git hooks."""
    check = subprocess.run(["lefthook", "check-install"], cwd=root, check=False)
    if check.returncode == 0:
        print("Lefthook hooks are already installed.")
        return
    if check.returncode != 1:
        raise RuntimeError(f"Unable to check Lefthook hooks (exit {check.returncode}).")
    subprocess.run(["lefthook", "install"], cwd=root, check=True)
    subprocess.run(["lefthook", "check-install"], cwd=root, check=True)
    print("Lefthook hooks installed.")


def check_commit_messages(
    base: str = "",
    head: str = "",
    root: Path = ROOT,
) -> None:
    """Validate incoming commit messages in base..head with convco."""
    event_base = base
    resolved_base = base
    if not resolved_base or resolved_base == ZERO_SHA:
        if _git_is_commit(root, "HEAD^"):
            resolved_base = subprocess.run(
                ["git", "rev-parse", "HEAD^"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        else:
            roots = subprocess.run(
                ["git", "rev-list", "--max-parents=0", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.splitlines()
            resolved_base = roots[0].strip() if roots else ""
    if not head or not _git_is_commit(root, head):
        print(f"No valid head ('{head or 'empty'}'); skipping commit-message check.")
        return
    if not resolved_base or not _git_is_commit(root, resolved_base):
        print(
            f"No valid base ref available (event base: '{event_base or 'empty'}'); "
            "skipping commit-message check."
        )
        return
    print(f"Checking commits {resolved_base}..{head}")
    subprocess.run(
        ["convco", "check", f"{resolved_base}..{head}"],
        cwd=root,
        check=True,
    )


def task_install_projects() -> dict[str, Any]:
    """Install the local project wheel without dependency resolution or build isolation."""
    return {
        "basename": "install-projects",
        "actions": [
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--no-build-isolation",
                "--force-reinstall",
                ".",
            ]
        ],
    }


def task_test() -> dict[str, Any]:
    """Run the package BDD suite."""
    return {
        "basename": "test",
        "task_dep": ["install-projects"],
        "actions": [[sys.executable, "-m", "pytest", "tests"]],
    }


def task_test_scripts() -> dict[str, Any]:
    """Run the repository automation and script tests."""
    return {
        "basename": "test-scripts",
        "actions": [[sys.executable, "-m", "pytest", "scripts/tests"]],
    }


def task_coverage() -> dict[str, Any]:
    """Run the package BDD suite with the .coveragerc coverage threshold."""
    return {
        "basename": "coverage",
        "task_dep": ["install-projects"],
        "actions": [
            [
                sys.executable,
                "-m",
                "pytest",
                "tests",
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=xml:coverage.xml",
            ]
        ],
        "clean": [clean_coverage],
    }


def task_lint() -> dict[str, Any]:
    """Lint Python files with ruff."""
    return {
        "basename": "lint",
        "actions": [["ruff", "check", "."]],
    }


def task_format_check() -> dict[str, Any]:
    """Verify Python formatting with ruff."""
    return {
        "basename": "format-check",
        "actions": [["ruff", "format", "--check", "."]],
    }


def task_typecheck() -> dict[str, Any]:
    """Typecheck package sources with mypy."""
    return {
        "basename": "typecheck",
        "actions": [["mypy", "src"]],
    }


def task_audit() -> dict[str, Any]:
    """Scan installed Python dependencies for known vulnerabilities."""
    return {
        "basename": "audit",
        "actions": [["pip-audit", "--local", "--skip-editable"]],
    }


def task_check_packages() -> dict[str, Any]:
    """Build wheel and sdist, run twine check, and inspect wheel contents."""
    return {
        "basename": "check-packages",
        "actions": [check_packages],
        "clean": [clean_distributions],
    }


def task_alint() -> dict[str, Any]:
    """Check repository structure rules from .alint.yml."""
    return {
        "basename": "alint",
        "actions": [["alint", "check"]],
    }


def task_lint_prose() -> dict[str, Any]:
    """Lint markdown prose with Vale."""
    return {
        "basename": "lint-prose",
        "actions": [["vale", "--no-global", *VALE_TARGETS]],
    }


def task_bun_install() -> dict[str, Any]:
    """Install frozen Bun developer CLIs from bun.lock."""
    return {
        "basename": "bun-install",
        "actions": [["bun", "install", "--frozen-lockfile"]],
    }


def task_docs_lint() -> dict[str, Any]:
    """Lint maintained markdown files with markdownlint-cli2."""
    return {
        "basename": "docs-lint",
        "task_dep": ["bun-install"],
        "actions": [
            [
                "bun",
                "x",
                "--bun",
                "--no-install",
                "markdownlint-cli2",
                *MARKDOWN_TARGETS,
            ]
        ],
    }


def task_actionlint() -> dict[str, Any]:
    """Lint GitHub Actions workflow files with actionlint."""
    return {
        "basename": "actionlint",
        "actions": [["actionlint", *_workflow_files()]],
    }


def task_install_hooks() -> dict[str, Any]:
    """Install or verify Lefthook git hooks."""
    return {
        "basename": "install-hooks",
        "actions": [install_hooks],
    }


def task_lint_commit() -> dict[str, Any]:
    """Validate a commit message read from stdin with convco."""
    return {
        "basename": "lint-commit",
        "actions": [["convco", "check", "--from-stdin", "--strip"]],
    }


def task_check_commit_messages() -> dict[str, Any]:
    """Validate incoming commit messages in a git range with convco."""
    return {
        "basename": "check-commit-messages",
        "params": [
            {
                "name": "base",
                "long": "base",
                "type": str,
                "default": "",
                "env_var": "COMMIT_BASE",
                "help": "Base commit SHA (defaults to HEAD^ or root commit when empty or zero).",
            },
            {
                "name": "head",
                "long": "head",
                "type": str,
                "default": "",
                "env_var": "COMMIT_HEAD",
                "help": "Head commit SHA to inspect.",
            },
        ],
        "actions": [check_commit_messages],
    }


def task_build_release() -> dict[str, Any]:
    """Build release distributions into dist/ and check tag/version and twine metadata."""
    return {
        "basename": "build-release",
        "params": [
            {
                "name": "ref_name",
                "long": "ref",
                "type": str,
                "default": "",
                "env_var": "GITHUB_REF_NAME",
                "help": "Git tag name (for example v0.1.0) to check against pyproject.toml.",
            }
        ],
        "actions": [build_release],
        "clean": [clean_dist],
    }


def task_pre_commit() -> dict[str, Any]:
    """Run all pre-commit checks."""
    return {
        "basename": "pre-commit",
        "task_dep": [
            "lint",
            "format-check",
            "typecheck",
            "lint-prose",
            "alint",
            "actionlint",
            "docs-lint",
        ],
        "actions": None,
    }


def task_policy() -> dict[str, Any]:
    """Run all local CI Policy checks."""
    return {
        "basename": "policy",
        "task_dep": [
            "lint",
            "format-check",
            "typecheck",
            "check-packages",
            "lint-prose",
            "alint",
            "actionlint",
        ],
        "actions": None,
    }


def task_docs() -> dict[str, Any]:
    """Run local documentation checks."""
    return {
        "basename": "docs",
        "task_dep": ["docs-lint", "lint-prose"],
        "actions": None,
    }


def task_ci() -> dict[str, Any]:
    """Run the full local CI suite."""
    return {
        "basename": "ci",
        "task_dep": ["policy", "docs-lint", "test-scripts", "coverage"],
        "actions": None,
    }

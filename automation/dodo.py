"""Unified repository task automation for Rude Clean Code (executed via doit)."""

from __future__ import annotations

import sys
from typing import Any

from automation.lib.git_checks import check_commit_messages, install_hooks
from automation.lib.packaging import (
    build_release,
    check_packages,
    clean_coverage,
    clean_dist,
    clean_distributions,
)
from automation.lib.quality import (
    MARKDOWN_TARGETS,
    PACKAGE_DIR,
    ROOT,
    VALE_TARGETS,
    dogfood_rude,
    workflow_files,
)

DOIT_CONFIG: dict[str, Any] = {
    "default_tasks": ["ci"],
    "verbosity": 2,
    "backend": "sqlite3",
    "dep_file": str(ROOT / ".doit.db"),
}


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
                f"./{PACKAGE_DIR}",
            ]
        ],
    }


def task_test() -> dict[str, Any]:
    """Run the package BDD suite."""
    return {
        "basename": "test",
        "task_dep": ["install-projects"],
        "actions": [[sys.executable, "-m", "pytest", f"{PACKAGE_DIR}/tests"]],
    }


def task_test_automation() -> dict[str, Any]:
    """Run the automation BDD, sandbox, and library tests."""
    return {
        "basename": "test-automation",
        "actions": [[sys.executable, "-m", "pytest", "automation/tests"]],
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
                f"{PACKAGE_DIR}/tests",
                f"--cov={PACKAGE_DIR}/src",
                "--cov-report=term-missing",
                "--cov-report=xml:coverage.xml",
            ]
        ],
        "clean": [clean_coverage],
    }


def task_dogfood() -> dict[str, Any]:
    """Run Rude using the installed clean-code plugin across repository Python sources."""
    return {
        "basename": "dogfood",
        "task_dep": ["install-projects"],
        "actions": [dogfood_rude],
    }


def task_lint() -> dict[str, Any]:
    """Lint Python files with ruff and dogfooded Rude CC rules."""
    return {
        "basename": "lint",
        "task_dep": ["dogfood"],
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
        "actions": [["mypy", f"{PACKAGE_DIR}/src"]],
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
        "actions": [["actionlint", *workflow_files()]],
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
        "task_dep": [
            "policy",
            "docs-lint",
            "test-automation",
            "coverage",
        ],
        "actions": None,
    }

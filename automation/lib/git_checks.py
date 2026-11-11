"""Git hook installation and Conventional Commit validation helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from automation.lib.quality import ROOT

ZERO_SHA = "0" * 40


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


def _resolve_commit_base(root: Path, base: str) -> str:
    if base and base != ZERO_SHA:
        return base
    if _git_is_commit(root, "HEAD^"):
        return subprocess.run(
            ["git", "rev-parse", "HEAD^"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    roots = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()
    return roots[0].strip() if roots else ""


def check_commit_messages(
    base: str = "",
    head: str = "",
    root: Path = ROOT,
) -> None:
    """Validate incoming commit messages in base..head with convco."""
    resolved_base = _resolve_commit_base(root, base)
    if not head or not _git_is_commit(root, head):
        print(f"No valid head ('{head or 'empty'}'); skipping commit-message check.")
        return
    if not resolved_base or not _git_is_commit(root, resolved_base):
        print(
            f"No valid base ref available (event base: '{base or 'empty'}'); "
            "skipping commit-message check."
        )
        return
    print(f"Checking commits {resolved_base}..{head}")
    subprocess.run(
        ["convco", "check", f"{resolved_base}..{head}"],
        cwd=root,
        check=True,
    )

"""BDD tests for git hook installation and commit message checks."""

import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(
    str(Path(__file__).resolve().parents[1] / "features" / "git_automation.feature")
)


@pytest.fixture
def git_state() -> dict[str, Any]:
    return {"invoked": [], "convco_calls": [], "commits": set(), "parent": None}


@given("Lefthook hooks are already installed")
def hooks_already_installed(
    dodo_module: ModuleType, monkeypatch: pytest.MonkeyPatch, git_state: dict[str, Any]
) -> None:
    def fake_run(
        cmd: list[str], *, cwd: Path, check: bool
    ) -> subprocess.CompletedProcess[str]:
        git_state["invoked"].append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)


@given("Lefthook hooks are not yet installed")
def hooks_need_install(
    dodo_module: ModuleType, monkeypatch: pytest.MonkeyPatch, git_state: dict[str, Any]
) -> None:
    statuses = iter([1, 0, 0])

    def fake_run(
        cmd: list[str], *, cwd: Path, check: bool
    ) -> subprocess.CompletedProcess[str]:
        git_state["invoked"].append(cmd)
        return subprocess.CompletedProcess(cmd, next(statuses))

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)


@given(parsers.parse("Lefthook hook verification exits with status {code:d}"))
def hooks_broken_status(
    dodo_module: ModuleType, monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    def fake_run(
        cmd: list[str], *, cwd: Path, check: bool
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, code)

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)


@when("install_hooks runs")
def run_install_hooks(
    dodo_module: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    git_state: dict[str, Any],
) -> None:
    try:
        dodo_module.install_hooks(root=tmp_path)
    except RuntimeError as exc:
        git_state["error"] = exc
    git_state["stdout"] = capsys.readouterr().out


@then(parsers.parse('only hook status verification runs and reports "{text}"'))
def verify_already_installed(git_state: dict[str, Any], text: str) -> None:
    assert git_state["invoked"] == [["lefthook", "check-install"]]
    assert text in git_state["stdout"]


@then(
    parsers.parse('Lefthook installs hooks, re-verifies status, and reports "{text}"')
)
def verify_fresh_install(git_state: dict[str, Any], text: str) -> None:
    assert git_state["invoked"] == [
        ["lefthook", "check-install"],
        ["lefthook", "install"],
        ["lefthook", "check-install"],
    ]
    assert text in git_state["stdout"]


@then(parsers.parse('hook installation fails with "{expected}"'))
def verify_hook_error(git_state: dict[str, Any], expected: str) -> None:
    assert expected in str(git_state["error"])


def _install_git_mock(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    git_state: dict[str, Any],
) -> None:
    def fake_run(
        cmd: list[str],
        *,
        cwd: Path,
        capture_output: bool = False,
        text: bool = False,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        if cmd[:3] == ["git", "cat-file", "-e"]:
            ref = cmd[3].removesuffix("^{commit}")
            code = 0 if ref in git_state["commits"] else 1
            return subprocess.CompletedProcess(cmd, code)
        if cmd[:3] == ["git", "rev-parse", "HEAD^"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=f"{git_state['parent']}\n"
            )
        if cmd[:3] == ["git", "rev-list", "--max-parents=0"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=f"{git_state['root_commit']}\n"
            )
        if cmd[:2] == ["convco", "check"]:
            git_state["convco_calls"].append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)


@given(
    parsers.parse('a git repository with commits "{c1}", "{c2}", and "{c3}"'),
)
def repo_with_commits(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    git_state: dict[str, Any],
    c1: str,
    c2: str,
    c3: str,
) -> None:
    git_state["commits"] = {c1, c2, c3}
    _install_git_mock(dodo_module, monkeypatch, git_state)


@given(
    parsers.parse(
        'a git repository with commits "{c1}", "{c2}", and "{c3}" where HEAD parent is "{parent}"'
    )
)
def repo_with_commits_and_parent(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    git_state: dict[str, Any],
    c1: str,
    c2: str,
    c3: str,
    parent: str,
) -> None:
    git_state["commits"] = {c1, c2, c3}
    git_state["parent"] = parent
    _install_git_mock(dodo_module, monkeypatch, git_state)


@given(
    parsers.parse(
        'a git repository without HEAD parent and root commit "{root_sha}" with head "{head}"'
    )
)
def repo_without_parent(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    git_state: dict[str, Any],
    root_sha: str,
    head: str,
) -> None:
    git_state["commits"] = {root_sha, head}
    git_state["root_commit"] = root_sha
    _install_git_mock(dodo_module, monkeypatch, git_state)


@when(
    parsers.re(
        r'commit messages are checked for base "(?P<base>[^"]*)" and head "(?P<head>[^"]*)"'
    )
)
def check_commits_explicit(
    dodo_module: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    git_state: dict[str, Any],
    base: str,
    head: str,
) -> None:
    dodo_module.check_commit_messages(base=base, head=head, root=tmp_path)
    git_state["stdout"] = capsys.readouterr().out


@when(
    parsers.parse('commit messages are checked for the zero SHA base and head "{head}"')
)
def check_commits_zero_sha(
    dodo_module: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    git_state: dict[str, Any],
    head: str,
) -> None:
    dodo_module.check_commit_messages(
        base=dodo_module.ZERO_SHA, head=head, root=tmp_path
    )
    git_state["stdout"] = capsys.readouterr().out


@then(parsers.parse('commit message validation skips with message "{expected}"'))
def verify_commit_skipped(git_state: dict[str, Any], expected: str) -> None:
    assert expected in git_state["stdout"]
    assert git_state["convco_calls"] == []


@then(parsers.parse('convco checks commit range "{commit_range}"'))
def verify_convco_range(git_state: dict[str, Any], commit_range: str) -> None:
    assert git_state["convco_calls"] == [["convco", "check", commit_range]]

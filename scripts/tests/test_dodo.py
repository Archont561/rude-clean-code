"""Tests for the unified doit automation tasks in dodo.py."""

import importlib.util
import subprocess
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import pytest
from doit.loader import load_tasks

ROOT = Path(__file__).resolve().parents[2]


def _load_dodo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("dodo", ROOT / "dodo.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_wheel(path: Path, entries: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for entry in entries:
            archive.writestr(entry, "")


def test_dodo_loads_expected_task_graph():
    dodo = _load_dodo()
    assert dodo.DOIT_CONFIG["default_tasks"] == ["ci"]
    assert dodo.DOIT_CONFIG["backend"] == "sqlite3"

    tasks = load_tasks(vars(dodo))
    by_name = {task.name: task for task in tasks}

    expected = {
        "install-projects",
        "test",
        "test-scripts",
        "coverage",
        "lint",
        "format-check",
        "typecheck",
        "audit",
        "check-packages",
        "alint",
        "lint-prose",
        "bun-install",
        "docs-lint",
        "actionlint",
        "install-hooks",
        "lint-commit",
        "check-commit-messages",
        "build-release",
        "pre-commit",
        "policy",
        "docs",
        "ci",
    }
    assert expected.issubset(by_name)
    assert "bun-install" in by_name["docs-lint"].task_dep
    for group in ("pre-commit", "policy", "docs", "ci"):
        assert set(by_name[group].task_dep).issubset(by_name)


def test_check_packages_cleans_builds_validates_and_strips_pythonpath(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dodo = _load_dodo()
    stale = tmp_path / "distributions"
    stale.mkdir()
    (stale / "stale.whl").write_text("old", encoding="utf-8")

    monkeypatch.setenv("PYTHONPATH", "/tmp/leaked-src")
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd, *, cwd, env, check):
        assert cwd == tmp_path
        assert check is True
        calls.append((cmd, env))
        if cmd[:3] == [sys.executable, "-m", "build"]:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            (outdir / "rude_clean_code-0.1.0.tar.gz").write_bytes(b"sdist")
            _write_wheel(
                outdir / "rude_clean_code-0.1.0-py3-none-any.whl",
                [
                    "rude_clean_code/__init__.py",
                    "rude_clean_code-0.1.0.dist-info/licenses/LICENSE",
                ],
            )
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo.subprocess, "run", fake_run)
    dodo.check_packages(root=tmp_path)

    assert not (stale / "stale.whl").exists()
    assert len(calls) == 2
    assert all("PYTHONPATH" not in env for _, env in calls)
    assert calls[1][0][:3] == [sys.executable, "-m", "twine"]
    assert "check" in calls[1][0]


@pytest.mark.parametrize(
    ("wheel_entries", "create_sdist", "expected_error"),
    [
        (["rude_clean_code/__init__.py"], False, "Expected one wheel and one sdist"),
        (["rude_clean_code/__init__.py"], True, "License missing"),
        (
            ["rude_clean_code-0.1.0.dist-info/licenses/LICENSE"],
            True,
            "Package initializer missing",
        ),
    ],
)
def test_check_packages_rejects_invalid_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wheel_entries: list[str],
    create_sdist: bool,
    expected_error: str,
):
    dodo = _load_dodo()

    def fake_run(cmd, *, cwd, env, check):
        if cmd[:3] == [sys.executable, "-m", "build"]:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            if create_sdist:
                (outdir / "pkg-0.1.0.tar.gz").write_bytes(b"sdist")
            _write_wheel(outdir / "pkg-0.1.0-py3-none-any.whl", wheel_entries)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match=expected_error):
        dodo.check_packages(root=tmp_path)


def test_build_release_rejects_mismatched_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dodo = _load_dodo()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "rude-clean-code"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("build should not run when tag mismatches")

    monkeypatch.setattr(dodo.subprocess, "run", fail_if_called)
    with pytest.raises(RuntimeError, match="does not match package version"):
        dodo.build_release(ref_name="v0.2.0", root=tmp_path)


def test_build_release_matches_tag_and_cleans_dist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dodo = _load_dodo()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "rude-clean-code"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    stale_dist = tmp_path / "dist"
    stale_dist.mkdir()
    (stale_dist / "stale.txt").write_text("stale", encoding="utf-8")

    monkeypatch.setenv("PYTHONPATH", "/tmp/leaked-src")
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd, *, cwd, env, check):
        assert cwd == tmp_path
        calls.append((cmd, env))
        if cmd[:3] == [sys.executable, "-m", "build"]:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / "pkg-0.1.0.tar.gz").write_bytes(b"sdist")
            (outdir / "pkg-0.1.0-py3-none-any.whl").write_bytes(b"whl")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo.subprocess, "run", fake_run)
    dodo.build_release(ref_name="v0.1.0", root=tmp_path)

    assert not (stale_dist / "stale.txt").exists()
    assert len(calls) == 2
    assert all("PYTHONPATH" not in env for _, env in calls)
    assert calls[1][0][:4] == [sys.executable, "-m", "twine", "check"]


def test_install_hooks_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    dodo = _load_dodo()
    invoked: list[list[str]] = []

    def already_installed(cmd, *, cwd, check):
        invoked.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo.subprocess, "run", already_installed)
    dodo.install_hooks(root=tmp_path)
    assert invoked == [["lefthook", "check-install"]]
    assert "already installed" in capsys.readouterr().out

    invoked.clear()
    statuses = iter([1, 0, 0])

    def needs_install(cmd, *, cwd, check):
        invoked.append(cmd)
        return subprocess.CompletedProcess(cmd, next(statuses))

    monkeypatch.setattr(dodo.subprocess, "run", needs_install)
    dodo.install_hooks(root=tmp_path)
    assert invoked == [
        ["lefthook", "check-install"],
        ["lefthook", "install"],
        ["lefthook", "check-install"],
    ]
    assert "hooks installed" in capsys.readouterr().out

    def broken_check(cmd, *, cwd, check):
        return subprocess.CompletedProcess(cmd, 2)

    monkeypatch.setattr(dodo.subprocess, "run", broken_check)
    with pytest.raises(RuntimeError, match="exit 2"):
        dodo.install_hooks(root=tmp_path)


def test_check_commit_messages_handles_empty_zero_and_valid_ranges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    dodo = _load_dodo()
    convco_calls: list[list[str]] = []
    commits = {"abc123", "def456", "HEAD^"}

    def fake_run(cmd, *, cwd, capture_output=False, text=False, check=False):
        if cmd[:3] == ["git", "cat-file", "-e"]:
            ref = cmd[3].removesuffix("^{commit}")
            return subprocess.CompletedProcess(cmd, 0 if ref in commits else 1)
        if cmd[:3] == ["git", "rev-parse", "HEAD^"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="abc123\n")
        if cmd[:2] == ["convco", "check"]:
            convco_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(dodo.subprocess, "run", fake_run)

    dodo.check_commit_messages(base="", head="", root=tmp_path)
    assert "skipping commit-message check" in capsys.readouterr().out
    assert convco_calls == []

    dodo.check_commit_messages(base="badref", head="def456", root=tmp_path)
    assert "No valid base ref available" in capsys.readouterr().out
    assert convco_calls == []

    dodo.check_commit_messages(base=dodo.ZERO_SHA, head="def456", root=tmp_path)
    assert convco_calls == [["convco", "check", "abc123..def456"]]


def test_check_commit_messages_root_fallback_without_head_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dodo = _load_dodo()
    convco_calls: list[list[str]] = []
    commits = {"rootsha", "def456"}

    def fake_run(cmd, *, cwd, capture_output=False, text=False, check=False):
        if cmd[:3] == ["git", "cat-file", "-e"]:
            ref = cmd[3].removesuffix("^{commit}")
            return subprocess.CompletedProcess(cmd, 0 if ref in commits else 1)
        if cmd[:3] == ["git", "rev-list", "--max-parents=0"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="rootsha\n")
        if cmd[:2] == ["convco", "check"]:
            convco_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0)
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(dodo.subprocess, "run", fake_run)
    dodo.check_commit_messages(base="", head="def456", root=tmp_path)
    assert convco_calls == [["convco", "check", "rootsha..def456"]]


def test_clean_helpers_remove_artifacts(tmp_path: Path):
    dodo = _load_dodo()
    (tmp_path / "coverage.xml").write_text("<xml/>", encoding="utf-8")
    (tmp_path / ".coverage").write_text("data", encoding="utf-8")
    (tmp_path / "distributions").mkdir()
    (tmp_path / "distributions" / "pkg.whl").write_bytes(b"whl")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "pkg.whl").write_bytes(b"whl")

    dodo.clean_coverage(root=tmp_path)
    dodo.clean_distributions(root=tmp_path)
    dodo.clean_dist(root=tmp_path)

    assert not (tmp_path / "coverage.xml").exists()
    assert not (tmp_path / ".coverage").exists()
    assert not (tmp_path / "distributions").exists()
    assert not (tmp_path / "dist").exists()

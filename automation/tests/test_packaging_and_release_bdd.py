"""BDD tests for package validation and release distribution builds."""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(
    str(
        Path(__file__).resolve().parents[1]
        / "features"
        / "packaging_and_release.feature"
    )
)

WHEEL_PRESETS: dict[str, list[str]] = {
    "initializer_only": ["rude_clean_code/__init__.py"],
    "license_only": ["rude_clean_code-0.1.0.dist-info/licenses/LICENSE"],
}


@pytest.fixture
def pkg_state() -> dict[str, Any]:
    return {"calls": []}


@given(
    "a temporary project workspace with stale distribution artifacts and leaked PYTHONPATH"
)
def workspace_with_stale_distributions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pkg_state: dict[str, Any]
) -> None:
    stale = tmp_path / "distributions"
    stale.mkdir()
    stale_file = stale / "stale.whl"
    stale_file.write_text("old", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", "/tmp/leaked-src")
    pkg_state["workspace"] = tmp_path
    pkg_state["stale_file"] = stale_file


@when("check_packages runs against a valid distribution build")
def run_check_packages_valid(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    write_wheel: Callable[[Path, list[str]], None],
    pkg_state: dict[str, Any],
) -> None:
    workspace = pkg_state["workspace"]
    calls: list[tuple[list[str], dict[str, str]]] = pkg_state["calls"]

    def fake_run(
        cmd: list[str], *, cwd: Path, env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert cwd == workspace
        assert check is True
        calls.append((cmd, env))
        if cmd[:3] == [sys.executable, "-m", "build"]:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            (outdir / "rude_clean_code-0.1.0.tar.gz").write_bytes(b"sdist")
            write_wheel(
                outdir / "rude_clean_code-0.1.0-py3-none-any.whl",
                [
                    "rude_clean_code/__init__.py",
                    "rude_clean_code-0.1.0.dist-info/licenses/LICENSE",
                ],
            )
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)
    dodo_module.check_packages(root=workspace)


@then("stale distribution artifacts are removed")
def check_stale_distributions_removed(pkg_state: dict[str, Any]) -> None:
    assert not pkg_state["stale_file"].exists()


@then("build and twine check run without PYTHONPATH")
def check_clean_pythonpath(pkg_state: dict[str, Any]) -> None:
    calls = pkg_state["calls"]
    assert len(calls) == 2
    assert all("PYTHONPATH" not in env for _, env in calls)


@then("twine validates both the sdist and wheel")
def check_twine_invoked_with_both(pkg_state: dict[str, Any]) -> None:
    twine_cmd = pkg_state["calls"][1][0]
    assert twine_cmd[:4] == [sys.executable, "-m", "twine", "check"]
    assert len(twine_cmd) == 6


@given("a temporary project workspace for validation")
def bare_validation_workspace(tmp_path: Path, pkg_state: dict[str, Any]) -> None:
    pkg_state["workspace"] = tmp_path


@when(
    parsers.parse(
        'check_packages inspects a wheel preset "{preset}" with sdist "{sdist_present}"'
    )
)
def run_check_packages_invalid(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    write_wheel: Callable[[Path, list[str]], None],
    pkg_state: dict[str, Any],
    preset: str,
    sdist_present: str,
) -> None:
    wheel_entries = WHEEL_PRESETS[preset]
    create_sdist = sdist_present == "present"

    def fake_run(
        cmd: list[str], *, cwd: Path, env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        if cmd[:3] == [sys.executable, "-m", "build"]:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            if create_sdist:
                (outdir / "pkg-0.1.0.tar.gz").write_bytes(b"sdist")
            write_wheel(outdir / "pkg-0.1.0-py3-none-any.whl", wheel_entries)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)
    try:
        dodo_module.check_packages(root=pkg_state["workspace"])
    except RuntimeError as exc:
        pkg_state["error"] = exc
    else:
        pytest.fail("Expected check_packages to raise RuntimeError")


@then(parsers.parse('package validation fails with "{expected}"'))
def verify_validation_error(pkg_state: dict[str, Any], expected: str) -> None:
    assert expected in str(pkg_state["error"])


@given(parsers.parse('a temporary project workspace with version "{version}"'))
def workspace_with_version(
    tmp_path: Path, pkg_state: dict[str, Any], version: str
) -> None:
    pkg_dir = tmp_path / "rude-clean-code"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "pyproject.toml").write_text(
        f'[project]\nname = "rude-clean-code"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    pkg_state["workspace"] = tmp_path


@given(
    parsers.parse(
        'a temporary project workspace with version "{version}", stale dist files, and leaked PYTHONPATH'
    )
)
def workspace_with_version_and_stale_dist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pkg_state: dict[str, Any],
    version: str,
) -> None:
    pkg_dir = tmp_path / "rude-clean-code"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "pyproject.toml").write_text(
        f'[project]\nname = "rude-clean-code"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    stale_dist = tmp_path / "dist"
    stale_dist.mkdir()
    stale_file = stale_dist / "stale.txt"
    stale_file.write_text("stale", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", "/tmp/leaked-src")
    pkg_state["workspace"] = tmp_path
    pkg_state["stale_dist_file"] = stale_file


@when(parsers.parse('build_release runs for tag "{tag}"'))
def run_build_release(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    pkg_state: dict[str, Any],
    tag: str,
) -> None:
    workspace = pkg_state["workspace"]
    calls: list[tuple[list[str], dict[str, str]]] = pkg_state["calls"]

    def fake_run(
        cmd: list[str], *, cwd: Path, env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        assert cwd == workspace
        calls.append((cmd, env))
        if cmd[:3] == [sys.executable, "-m", "build"]:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / "pkg-0.1.0.tar.gz").write_bytes(b"sdist")
            (outdir / "pkg-0.1.0-py3-none-any.whl").write_bytes(b"whl")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)
    try:
        dodo_module.build_release(ref_name=tag, root=workspace)
    except RuntimeError as exc:
        pkg_state["error"] = exc


@then(
    parsers.parse(
        'the release build fails with "{expected}" before running subprocesses'
    )
)
def verify_release_mismatch(pkg_state: dict[str, Any], expected: str) -> None:
    assert "error" in pkg_state
    assert expected in str(pkg_state["error"])
    assert pkg_state["calls"] == []


@when("build_release runs without a tag")
def run_build_release_dry_run(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    pkg_state: dict[str, Any],
) -> None:
    run_build_release(dodo_module, monkeypatch, pkg_state, tag="")


@when("build_release produces only a wheel without an sdist")
def run_build_release_incomplete_dist(
    dodo_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    pkg_state: dict[str, Any],
) -> None:
    workspace = pkg_state["workspace"]

    def fake_run(
        cmd: list[str], *, cwd: Path, env: dict[str, str], check: bool
    ) -> subprocess.CompletedProcess[str]:
        if cmd[:3] == [sys.executable, "-m", "build"]:
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / "pkg-0.1.0-py3-none-any.whl").write_bytes(b"whl")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(dodo_module.subprocess, "run", fake_run)
    try:
        dodo_module.build_release(ref_name="", root=workspace)
    except RuntimeError as exc:
        pkg_state["error"] = exc
    else:
        pytest.fail("Expected build_release to raise RuntimeError")


@then(parsers.parse('the release build fails with "{expected}"'))
def verify_release_error(pkg_state: dict[str, Any], expected: str) -> None:
    assert "error" in pkg_state
    assert expected in str(pkg_state["error"])


@then("stale dist files are removed")
def verify_stale_dist_removed(pkg_state: dict[str, Any]) -> None:
    assert not pkg_state["stale_dist_file"].exists()


@then("build and twine check run without PYTHONPATH for release artifacts")
def verify_release_subprocesses(pkg_state: dict[str, Any]) -> None:
    assert "error" not in pkg_state
    calls = pkg_state["calls"]
    assert len(calls) == 2
    assert all("PYTHONPATH" not in env for _, env in calls)
    assert calls[1][0][:4] == [sys.executable, "-m", "twine", "check"]

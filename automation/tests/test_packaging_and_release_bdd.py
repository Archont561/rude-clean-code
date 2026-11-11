"""BDD tests for package validation and release distribution builds."""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from automation.lib import packaging

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

    monkeypatch.setattr(packaging.subprocess, "run", fake_run)
    packaging.check_packages(root=workspace)


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


@pytest.fixture
def inspect_invalid_package(
    monkeypatch: pytest.MonkeyPatch,
    write_wheel: Callable[[Path, list[str]], None],
    pkg_state: dict[str, Any],
) -> Callable[[str, str], None]:
    def _run(preset: str, sdist_present: str) -> None:
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

        monkeypatch.setattr(packaging.subprocess, "run", fake_run)
        try:
            packaging.check_packages(root=pkg_state["workspace"])
        except RuntimeError as exc:
            pkg_state["error"] = exc
        else:
            pytest.fail("Expected check_packages to raise RuntimeError")

    return _run


@when(
    parsers.parse(
        'check_packages inspects a wheel preset "{preset}" with sdist "{sdist_present}"'
    )
)
def run_check_packages_invalid(
    inspect_invalid_package: Callable[[str, str], None],
    preset: str,
    sdist_present: str,
) -> None:
    inspect_invalid_package(preset, sdist_present)


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

    monkeypatch.setattr(packaging.subprocess, "run", fake_run)
    try:
        packaging.build_release(ref_name=tag, root=workspace)
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
    monkeypatch: pytest.MonkeyPatch,
    pkg_state: dict[str, Any],
) -> None:
    run_build_release(monkeypatch, pkg_state, tag="")


@when("build_release produces only a wheel without an sdist")
def run_build_release_incomplete_dist(
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

    monkeypatch.setattr(packaging.subprocess, "run", fake_run)
    try:
        packaging.build_release(ref_name="", root=workspace)
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


@given(
    parsers.parse(
        'a temporary project workspace with version "{version}", built dist artifacts, and leaked PYTHONPATH'
    )
)
def workspace_with_built_dist(
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
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / f"rude_clean_code-{version}.tar.gz").write_bytes(b"sdist")
    (dist_dir / f"rude_clean_code-{version}-py3-none-any.whl").write_bytes(b"whl")
    monkeypatch.setenv("PYTHONPATH", "/tmp/leaked-src")
    pkg_state["workspace"] = tmp_path


@when("github_release runs without a tag")
def run_github_release_no_tag(
    monkeypatch: pytest.MonkeyPatch, pkg_state: dict[str, Any]
) -> None:
    _invoke_github_release(monkeypatch, pkg_state, tag="", convco_stdout="")


@when(parsers.parse('github_release runs for tag "{tag}"'))
def run_github_release_for_tag(
    monkeypatch: pytest.MonkeyPatch, pkg_state: dict[str, Any], tag: str
) -> None:
    _invoke_github_release(monkeypatch, pkg_state, tag=tag, convco_stdout="")


@when(parsers.parse('github_release runs for tag "{tag}" with convco section output'))
def run_github_release_with_convco(
    monkeypatch: pytest.MonkeyPatch, pkg_state: dict[str, Any], tag: str
) -> None:
    sample = (
        "# Changelog\n\n"
        "All notable changes to rude-clean-code are documented here.\n\n"
        f"## [{tag}](https://example.com/compare/v0.1.0...{tag}) (2026-11-11)\n\n"
        "### Features\n\n"
        "* **rules:** add rules\n"
    )
    _invoke_github_release(monkeypatch, pkg_state, tag=tag, convco_stdout=sample)


@when(parsers.parse('github_release runs for tag "{tag}" with empty convco output'))
def run_github_release_empty_convco(
    monkeypatch: pytest.MonkeyPatch, pkg_state: dict[str, Any], tag: str
) -> None:
    sample = (
        "# Changelog\n\nAll notable changes to rude-clean-code are documented here.\n"
    )
    _invoke_github_release(monkeypatch, pkg_state, tag=tag, convco_stdout=sample)


def _invoke_github_release(
    monkeypatch: pytest.MonkeyPatch,
    pkg_state: dict[str, Any],
    *,
    tag: str,
    convco_stdout: str,
) -> None:
    workspace = pkg_state["workspace"]
    calls: list[tuple[list[str], dict[str, str]]] = pkg_state["calls"]

    def fake_run(
        cmd: list[str], *, cwd: Path, env: dict[str, str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        assert cwd == workspace
        calls.append((cmd, env))
        if cmd[0] == "convco":
            return subprocess.CompletedProcess(cmd, 0, stdout=convco_stdout, stderr="")
        if "--notes-file" in cmd:
            notes_path = Path(cmd[cmd.index("--notes-file") + 1])
            pkg_state["captured_notes"] = notes_path.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(packaging.subprocess, "run", fake_run)
    try:
        packaging.github_release(ref_name=tag, root=workspace)
    except RuntimeError as exc:
        pkg_state["error"] = exc


@then(
    parsers.parse(
        'the GitHub release fails with "{expected}" before running subprocesses'
    )
)
def verify_github_release_error(pkg_state: dict[str, Any], expected: str) -> None:
    assert "error" in pkg_state
    assert expected in str(pkg_state["error"])
    assert pkg_state["calls"] == []


@then(
    "convco and gh release create run without PYTHONPATH using the extracted release notes"
)
def verify_github_release_with_notes(pkg_state: dict[str, Any]) -> None:
    assert "error" not in pkg_state
    calls = pkg_state["calls"]
    assert len(calls) == 2
    assert calls[0][0][:4] == ["convco", "changelog", "--max-versions", "1"]
    assert calls[1][0][:4] == ["gh", "release", "create", "v0.2.0"]
    assert "--notes-file" in calls[1][0]
    assert "--verify-tag" in calls[1][0]
    assert all("PYTHONPATH" not in env for _, env in calls)
    assert pkg_state["captured_notes"].startswith("## [v0.2.0]")
    assert "### Features" in pkg_state["captured_notes"]


@then("gh release create runs with --generate-notes and both distributions")
def verify_github_release_generated_notes(pkg_state: dict[str, Any]) -> None:
    assert "error" not in pkg_state
    calls = pkg_state["calls"]
    assert len(calls) == 2
    gh_cmd = calls[1][0]
    assert gh_cmd[:4] == ["gh", "release", "create", "v0.2.0"]
    assert "--generate-notes" in gh_cmd
    assert "--verify-tag" in gh_cmd
    assert any(arg.endswith(".whl") for arg in gh_cmd)
    assert any(arg.endswith(".tar.gz") for arg in gh_cmd)
    assert all("PYTHONPATH" not in env for _, env in calls)

"""Unit tests for automation.lib.activate PYTHONPATH discovery."""

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from automation.lib import activate


def test_python_path_collects_src_dirs_and_preserves_caller_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pkg = tmp_path / "alpha"
    (pkg / "src").mkdir(parents=True)
    (pkg / "pyproject.toml").write_text('[project]\nname = "alpha"\n', encoding="utf-8")
    no_src = tmp_path / "docs-only"
    no_src.mkdir()
    (no_src / "pyproject.toml").write_text("[tool.other]\n", encoding="utf-8")

    def fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        stdout = b"alpha/pyproject.toml\x00docs-only/pyproject.toml\x00"
        return subprocess.CompletedProcess([], 0, stdout=stdout, stderr=b"")

    monkeypatch.setattr(activate.subprocess, "run", fake_run)
    alpha_src = str(pkg / "src")
    joined = activate.python_path(tmp_path, f"/custom/lib{os.pathsep}{alpha_src}")
    assert joined.split(os.pathsep) == [alpha_src, "/custom/lib"]


def test_main_reads_pixi_project_root_and_prints_pythonpath(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PIXI_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("PYTHONPATH", "/existing")
    monkeypatch.setattr(activate, "python_path", lambda root, cur: f"{root}:{cur}")
    activate.main()
    assert capsys.readouterr().out.strip() == f"{tmp_path}:/existing"

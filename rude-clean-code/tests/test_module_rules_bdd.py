"""BDD steps for CC001-CC005 module and package organization rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios(
    str(Path(__file__).resolve().parents[1] / "features" / "module_rules.feature")
)


@pytest.fixture
def mod_state(tmp_path: Path) -> dict[str, object]:
    return {"root": tmp_path, "targets": []}


def _write_file(root: Path, rel_path: str, content: str) -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@given("a temporary module project with CC001 max_lines set to 12")
def configure_cc001_project(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(
        '[tool.rude]\nselect = ["CC001"]\n\n[tool.rude.rules.CC001]\nmax_lines = 12\n',
        encoding="utf-8",
    )


@given("a Python module with two separate symbol clusters exceeding 12 lines")
def write_clustered_module(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    target = _write_file(
        root,
        "pkg/service.py",
        (
            "def _alpha_step():\n"
            "    return 1\n\n"
            "def run_alpha():\n"
            "    return _alpha_step()\n\n"
            "class BetaJob:\n"
            "    def run(self):\n"
            "        return 2\n\n"
            "def run_beta():\n"
            "    return BetaJob().run()\n\n"
            "EXTRA = 1\n"
        ),
    )
    mod_state["targets"] = [str(target)]


@given("a temporary module project checking CC002 with VERSION allowed")
def configure_cc002_project(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(
        '[tool.rude]\nselect = ["CC002"]\n\n'
        '[tool.rude.rules.CC002]\nallowed_names = ["VERSION"]\n',
        encoding="utf-8",
    )


@given(
    "a package initializer with VERSION, TYPE_CHECKING, __all__, and a helper function"
)
def write_mixed_init(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    target = _write_file(
        root,
        "pkg/__init__.py",
        (
            '"""Package."""\n'
            "from importlib.metadata import version as _version\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from .types import Item\n\n"
            'VERSION = _version("pkg")\n'
            '__all__ = ["VERSION"]\n\n'
            "def leak_helper():\n"
            "    return 1\n"
        ),
    )
    mod_state["targets"] = [str(target)]


@given("a temporary module project checking CC003")
def configure_cc003_project(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(
        '[tool.rude]\nselect = ["CC003"]\n',
        encoding="utf-8",
    )


@given("an empty marker __init__.py alongside a non-empty __init__.py missing __all__")
def write_marker_and_nonempty_inits(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    marker = _write_file(root, "pkg/rules/__init__.py", '"""Marker package."""\n')
    missing = _write_file(root, "pkg/api/__init__.py", "from .core import PublicApi\n")
    mod_state["targets"] = [str(marker), str(missing)]


@given("a temporary module project checking CC004 and CC005")
def configure_cc004_cc005_project(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(
        '[tool.rude]\nselect = ["CC004", "CC005"]\n',
        encoding="utf-8",
    )


@given(
    "a module with a 3-dot relative import and __all__ containing a private name and a dunder"
)
def write_relative_and_all_module(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    assert isinstance(root, Path)
    target = _write_file(
        root,
        "pkg/sub/deep.py",
        (
            "from ...root import item\n"
            '__all__ = ["Public", "_private_api", "__version__"]\n'
        ),
    )
    mod_state["targets"] = [str(target)]


@when("Rude runs CC0 checks on the module project")
def run_rude_cc0(mod_state: dict[str, object]) -> None:
    root = mod_state["root"]
    targets = mod_state["targets"]
    assert isinstance(root, Path)
    assert isinstance(targets, list)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rude",
            "check",
            "--config",
            str(root / "pyproject.toml"),
            "--format",
            "json",
            *targets,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    mod_state["returncode"] = result.returncode
    mod_state["stderr"] = result.stderr
    mod_state["diagnostics"] = [
        json.loads(line) for line in result.stdout.splitlines() if line.strip()
    ]


@then("Rude reports CC001 without an autofix and suggests splitting by clusters")
def assert_cc001_split_no_fix(mod_state: dict[str, object]) -> None:
    assert mod_state["returncode"] == 0, mod_state["stderr"]
    diags = mod_state["diagnostics"]
    assert isinstance(diags, list)
    assert len(diags) == 1
    assert diags[0]["code"] == "CC001"
    assert diags[0]["fixable"] is False
    assert "service/__init__.py" in diags[0]["message"]
    assert "clusters" in diags[0]["message"]


@then("Rude flags only the helper function in __init__.py at INFO severity")
def assert_cc002_flags_only_helper(mod_state: dict[str, object]) -> None:
    assert mod_state["returncode"] == 0, mod_state["stderr"]
    diags = mod_state["diagnostics"]
    assert isinstance(diags, list)
    assert len(diags) == 1
    assert diags[0]["code"] == "CC002"
    assert diags[0]["severity"] == "info"
    assert "leak_helper" in diags[0]["message"]
    assert "VERSION" not in diags[0]["message"]


@then("Rude flags only the non-empty __init__.py for missing __all__")
def assert_cc003_flags_non_empty_only(mod_state: dict[str, object]) -> None:
    assert mod_state["returncode"] == 0, mod_state["stderr"]
    diags = mod_state["diagnostics"]
    assert isinstance(diags, list)
    assert len(diags) == 1
    assert diags[0]["code"] == "CC003"
    assert diags[0]["severity"] == "warning"
    assert diags[0]["file"].endswith("pkg/api/__init__.py")


@then("Rude reports CC004 and CC005 while keeping __version__ exempt")
def assert_cc004_cc005_and_dunder_exempt(mod_state: dict[str, object]) -> None:
    assert mod_state["returncode"] == 0, mod_state["stderr"]
    diags = mod_state["diagnostics"]
    assert isinstance(diags, list)
    assert [d["code"] for d in sorted(diags, key=lambda x: x["line"])] == [
        "CC004",
        "CC005",
    ]
    assert "_private_api" in diags[-1]["message"]
    assert all("__version__" not in d["message"] for d in diags)

"""Shared fixtures for automation BDD and library tests."""

import importlib.util
import sys
import zipfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def pytest_configure() -> None:
    """Ensure the repository root is importable when running automation tests."""
    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory."""
    return ROOT


@pytest.fixture
def dodo_module(repo_root: Path) -> ModuleType:
    """Load automation/dodo.py as an isolated module instance."""
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    spec = importlib.util.spec_from_file_location(
        "dodo", repo_root / "automation" / "dodo.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def write_wheel() -> Callable[[Path, list[str]], None]:
    """Return a helper that writes a minimal wheel archive with given entries."""

    def _write(path: Path, entries: list[str]) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            for entry in entries:
                archive.writestr(entry, "")

    return _write

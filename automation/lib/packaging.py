"""Packaging validation, artifact cleanup, and release build helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from collections.abc import Sequence
from pathlib import Path

from automation.lib.quality import PACKAGE_DIR, ROOT


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def _run_isolated(args: Sequence[str], *, cwd: Path = ROOT) -> None:
    subprocess.run(list(args), cwd=cwd, env=_clean_env(), check=True)


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


def _verify_wheel_contents(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
            raise RuntimeError(f"License missing from {wheel.name}")
        if "rude_clean_code/__init__.py" not in names:
            raise RuntimeError(f"Package initializer missing from {wheel.name}")


def check_packages(
    root: Path = ROOT,
    sources: Sequence[Path] | None = None,
) -> None:
    """Build wheel and sdist into distributions/, run twine check, and inspect wheels."""
    package_sources = tuple(sources) if sources is not None else (root / PACKAGE_DIR,)
    outputs = root / "distributions"
    shutil.rmtree(outputs, ignore_errors=True)
    outputs.mkdir(parents=True, exist_ok=True)
    for source in package_sources:
        build_cmd = [
            sys.executable,
            "-m",
            "build",
            str(source),
            "--outdir",
            str(outputs),
        ]
        _run_isolated(build_cmd, cwd=root)
    files = sorted(outputs.iterdir())
    if len(files) != 2 * len(package_sources):
        raise RuntimeError("Expected one wheel and one sdist per distribution")
    twine_cmd = [sys.executable, "-m", "twine", "check", *(str(p) for p in files)]
    _run_isolated(twine_cmd, cwd=root)
    for wheel in sorted(outputs.glob("*.whl")):
        _verify_wheel_contents(wheel)


def build_release(ref_name: str = "", root: Path = ROOT) -> None:
    """Verify an optional release tag matches pyproject.toml, build dist/, and run twine check."""
    package_root = root / PACKAGE_DIR
    if ref_name:
        tag = ref_name.removeprefix("v")
        manifest = tomllib.loads(
            (package_root / "pyproject.toml").read_text(encoding="utf-8")
        )
        package_version = manifest["project"]["version"]
        if tag != package_version:
            raise RuntimeError(
                f"Tag '{ref_name}' does not match package version '{package_version}'."
            )
    dist_dir = root / "dist"
    shutil.rmtree(dist_dir, ignore_errors=True)
    _run_isolated(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir), str(package_root)],
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

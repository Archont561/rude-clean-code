"""Build, validate, and smoke-test the distributions in an isolated environment."""

import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("rude-clean-code",)


def run(*args: str) -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def main() -> None:
    outputs = ROOT / "distributions"
    outputs.mkdir(exist_ok=True)
    for package in PACKAGES:
        run(
            sys.executable,
            "-m",
            "build",
            str(ROOT / "packages" / package),
            "--outdir",
            str(outputs),
        )
    files = sorted(outputs.iterdir())
    if len(files) != 2 * len(PACKAGES):
        raise RuntimeError("Expected one wheel and one sdist per distribution")
    run(sys.executable, "-m", "twine", "check", *(str(path) for path in files))
    wheels = sorted(outputs.glob("*.whl"))
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
                raise RuntimeError(f"License missing from {wheel.name}")
            if "rude_clean_code/__init__.py" not in names:
                raise RuntimeError(f"Package initializer missing from {wheel.name}")


if __name__ == "__main__":
    main()

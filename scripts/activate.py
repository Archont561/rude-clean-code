"""Print the Python path for Pixi activation, discovering local src layouts."""

import os
import subprocess
from pathlib import Path


def python_path(root: Path, current: str) -> str:
    """Find tracked or unignored Python projects and preserve the caller's path."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--deduplicate",
            "-z",
            "--",
            ":(glob)**/pyproject.toml",
        ],
        check=True,
        capture_output=True,
    )
    sources = set()
    for name in result.stdout.split(b"\0"):
        if name:
            project = root / os.fsdecode(name)
            source = project.parent / "src"
            if project.is_file() and source.is_dir():
                sources.add(str(source))
    existing = current.split(os.pathsep) if current else []
    return os.pathsep.join(
        [*sorted(sources), *(p for p in existing if p not in sources)]
    )


def main() -> None:
    root = Path(os.environ["PIXI_PROJECT_ROOT"])
    print(python_path(root, os.environ.get("PYTHONPATH", "")))


if __name__ == "__main__":
    main()

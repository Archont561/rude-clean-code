import json
import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios(
    str(Path(__file__).resolve().parents[1] / "features" / "package_version.feature")
)


@pytest.fixture
def package_state():
    return {}


@given("the package is installed")
def package_is_installed():
    assert version("rude-clean-code")


@when("its root namespace is inspected")
def inspect_root_namespace(package_state):
    # A fresh interpreter avoids attributes added by earlier submodule imports.
    script = """import json, rude_clean_code as package
print(json.dumps({
    'public_names': [name for name in vars(package) if not name.startswith('_')],
    'exports': package.__all__,
    'version': package.VERSION,
}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    package_state.update(json.loads(result.stdout))


@then("VERSION is its only public export")
def only_version_is_public(package_state):
    assert package_state["exports"] == ["VERSION"]
    assert package_state["public_names"] == ["VERSION"]


@then("VERSION matches pyproject and installed distribution metadata")
def version_matches_distribution(package_state):
    assert isinstance(package_state["version"], str)
    manifest = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project_version = tomllib.loads(manifest.read_text(encoding="utf-8"))["project"][
        "version"
    ]
    assert package_state["version"] == project_version == version("rude-clean-code")


@then("VERSION is read from distribution metadata")
def version_is_read_from_metadata():
    script = """from unittest.mock import patch
with patch('importlib.metadata.version', return_value='9.8.7') as get_version:
    import rude_clean_code as package
    assert package.VERSION == '9.8.7'
    get_version.assert_called_once_with('rude-clean-code')
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


@then("the package has no other source files")
def only_initializer_in_source():
    source = Path(__file__).resolve().parents[1] / "src" / "rude_clean_code"
    files = [
        p.relative_to(source).as_posix()
        for p in source.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ]
    assert files == ["__init__.py"]

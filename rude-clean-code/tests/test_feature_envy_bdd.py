"""BDD steps for the CC606 Feature Envy indicator and CC605 dunder escalation (RCC-13/14)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

FEATURE_ENVY_TOML = """
[tool.rude]
select = ["CC606"]
"""

DUNDERS_TOML = """
[tool.rude]
select = ["CC605"]

[tool.rude.rules.CC605]
flagged_dunders = ["__code__"]
"""

ENVY_SAMPLE = """
from tasknest.task import TaskDefinition


def same_task(candidate: TaskDefinition, dep: TaskDefinition) -> bool:
    return candidate.source_path == dep.source_path
"""

CLEAN_SAMPLE = """
from tasknest.task import TaskDefinition


def compare_names(left: str, right: str) -> bool:
    return left.upper() == right.upper()


class TaskDefinition:
    def __eq__(self, other: "TaskDefinition") -> bool:
        return self.source_path == other.source_path
"""

DUNDER_SAMPLE = """
def inspect(fn, other):
    return fn.__code__.co_filename, other.__name__
"""

scenarios(
    str(Path(__file__).resolve().parents[1] / "features" / "feature_envy.feature")
)


@pytest.fixture
def envy_state(tmp_path: Path) -> dict[str, object]:
    return {"root": tmp_path}


def _run_rude(root: Path, targets: list[Path]) -> list[dict[str, object]]:
    cmd = [
        sys.executable,
        "-m",
        "rude",
        "check",
        "--config",
        str(root / "pyproject.toml"),
        "--format",
        "json",
        *(str(target) for target in targets),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return [json.loads(line) for line in res.stdout.splitlines() if line.strip()]


@given("a temporary project configured with the CC606 Feature Envy indicator")
def setup_envy_config(envy_state: dict[str, object]) -> None:
    root = envy_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(FEATURE_ENVY_TOML, encoding="utf-8")


@given("a module whose helper compares two instances of an imported type")
def write_envy_module(envy_state: dict[str, object]) -> None:
    root = envy_state["root"]
    assert isinstance(root, Path)
    (root / "graph.py").write_text(ENVY_SAMPLE, encoding="utf-8")


@given("a module whose helpers compare builtin values or live on the type itself")
def write_clean_module(envy_state: dict[str, object]) -> None:
    root = envy_state["root"]
    assert isinstance(root, Path)
    (root / "clean.py").write_text(CLEAN_SAMPLE, encoding="utf-8")


@when("Rude checks the Feature Envy workspace")
def run_envy_check(envy_state: dict[str, object]) -> None:
    root = envy_state["root"]
    assert isinstance(root, Path)
    envy_state["diagnostics"] = _run_rude(root, [root / "graph.py", root / "clean.py"])


@then("CC606 reports the external same-type pair with indicator wording")
def assert_envy_reported(envy_state: dict[str, object]) -> None:
    diags = envy_state["diagnostics"]
    assert isinstance(diags, list)
    reported = [d for d in diags if d["code"] == "CC606"]
    assert reported, diags
    hit = reported[0]
    assert hit["severity"] == "info"
    assert hit["file"].endswith("graph.py")
    message = str(hit["message"])
    assert "TaskDefinition" in message
    assert "Feature Envy" in message
    assert "violat" not in message.lower()


@then("CC606 stays silent for builtin annotations and in-type comparison methods")
def assert_envy_silence(envy_state: dict[str, object]) -> None:
    diags = envy_state["diagnostics"]
    assert isinstance(diags, list)
    clean_hits = [d for d in diags if d["code"] == "CC606"]
    assert not [d for d in clean_hits if d["file"].endswith("clean.py")]


@given("a temporary project configured with flagged CC605 dunders")
def setup_dunder_config(envy_state: dict[str, object]) -> None:
    root = envy_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(DUNDERS_TOML, encoding="utf-8")


@given("a module reading escalated and non-escalated dunder members")
def write_dunder_module(envy_state: dict[str, object]) -> None:
    root = envy_state["root"]
    assert isinstance(root, Path)
    (root / "inspect_module.py").write_text(DUNDER_SAMPLE, encoding="utf-8")


@when("Rude checks the dunder workspace")
def run_dunder_check(envy_state: dict[str, object]) -> None:
    root = envy_state["root"]
    assert isinstance(root, Path)
    envy_state["diagnostics"] = _run_rude(root, [root / "inspect_module.py"])


@then("CC605 reports only the escalated dunder members")
def assert_dunder_reported(envy_state: dict[str, object]) -> None:
    diags = envy_state["diagnostics"]
    assert isinstance(diags, list)
    reported = [d for d in diags if d["code"] == "CC605"]
    assert len(reported) == 1, reported
    assert "__code__" in str(reported[0]["message"])


@then("CC605 keeps ordinary protocol dunders silent")
def assert_dunder_silence(envy_state: dict[str, object]) -> None:
    diags = envy_state["diagnostics"]
    assert isinstance(diags, list)
    reported = [d for d in diags if d["code"] == "CC605"]
    assert all("__name__" not in str(d["message"]) for d in reported)

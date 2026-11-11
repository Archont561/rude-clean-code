"""BDD steps for maturing heuristic (RCC-6/11) and CC9xx documentation (RCC-7/12) rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

STRICT_MATURING_TOML = """
[tool.rude]
select = ["CC105", "CC106", "CC108", "CC204", "CC205", "CC206", "CC304", "CC305", "CC307", "CC503", "CC504", "CC602", "CC603", "CC604", "CC605"]
"""

MATURING_SAMPLE = """
class ExternalSub(ExternalBase):
    def run(self):
        raise NotImplementedError


class Coordinator:
    def __init__(self, a: A, b: B, c: C, d: D, e: E, f: F) -> None:
        self.a = a


def process(items, unused_opt, dry_run: bool = False):
    if not dry_run:
        res = items.a.b.c.d
    else:
        res = items._secret
    return res
"""

DOCS_COMMENTS_TOML = """
[tool.rude]
select = ["CC9"]

[tool.rude.rules.CC903]
keywords = ["TODO", "FIXME", "HACK"]

[tool.rude.rules.CC906]
require_reason_for = ["CC6"]
"""

DOCS_SRC_SAMPLE = '''
"""Module docs."""

def api(alpha: int) -> None:
    """Stub docs.

    Args:
        alpha: Active arg.
        ghost: Removed arg.

    Returns:
        Nothing really.
    """
    # TODO: missing ticket
    # TODO
    # old_x = 1
    # old_y = 2
    x = 1  # noqa
    y = 2  # noqa: CC601
    "dangling literal"


def empty_doc() -> None:
    """..."""
    pass
'''

DOCS_TEST_SAMPLE = """
def test_helper() -> None:
    # TODO: allowed inside tests
    pass
"""

scenarios(
    str(
        Path(__file__).resolve().parents[1]
        / "features"
        / "maturing_and_documentation_rules.feature"
    )
)


@pytest.fixture
def m4_state(tmp_path: Path) -> dict[str, object]:
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


@given("a temporary project configured with maturing Strict heuristics")
def setup_strict_maturing(m4_state: dict[str, object]) -> None:
    root = m4_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(STRICT_MATURING_TOML, encoding="utf-8")


@given("a Python module combining heuristic smells and an external subclass")
def write_maturing_module(m4_state: dict[str, object]) -> None:
    root = m4_state["root"]
    assert isinstance(root, Path)
    (root / "app.py").write_text(MATURING_SAMPLE, encoding="utf-8")


@when("Rude checks the maturing module")
def run_maturing_check(m4_state: dict[str, object]) -> None:
    root = m4_state["root"]
    assert isinstance(root, Path)
    m4_state["diagnostics"] = _run_rude(root, [root / "app.py"])


@then("maturing heuristic diagnostics emit INFO indicator messages")
def assert_maturing_diags(m4_state: dict[str, object]) -> None:
    diags = m4_state["diagnostics"]
    assert isinstance(diags, list)
    codes = {d["code"] for d in diags}
    assert {"CC105", "CC106", "CC204", "CC307", "CC604", "CC605"} <= codes
    for diag in diags:
        if diag["code"] != "CC504":
            assert diag["severity"] == "info"
        assert "violat" not in str(diag["message"]).lower()


@then("absent external base rules emit no false override or segregation claims")
def assert_absent_base_silence(m4_state: dict[str, object]) -> None:
    diags = m4_state["diagnostics"]
    assert isinstance(diags, list)
    codes = {d["code"] for d in diags}
    assert not (codes & {"CC305", "CC602", "CC603"})


@given("a temporary project configured with CC9xx documentation and comment rules")
def setup_cc9_config(m4_state: dict[str, object]) -> None:
    root = m4_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(DOCS_COMMENTS_TOML, encoding="utf-8")


@given("source and test modules exercising docstring drift, suppressions, and TODOs")
def write_docs_workspace(m4_state: dict[str, object]) -> None:
    root = m4_state["root"]
    assert isinstance(root, Path)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "src" / "service.py").write_text(DOCS_SRC_SAMPLE, encoding="utf-8")
    (root / "tests" / "test_service.py").write_text(DOCS_TEST_SAMPLE, encoding="utf-8")


@when("Rude checks the documentation workspace")
def run_docs_check(m4_state: dict[str, object]) -> None:
    root = m4_state["root"]
    assert isinstance(root, Path)
    m4_state["diagnostics"] = _run_rude(root, [root / "src", root / "tests"])


@then(
    "CC9xx diagnostics report documentation and comment hygiene issues with expected severities"
)
def assert_cc9_diags(m4_state: dict[str, object]) -> None:
    diags = m4_state["diagnostics"]
    assert isinstance(diags, list)
    by_code: dict[str, list[dict[str, object]]] = {}
    for diag in diags:
        by_code.setdefault(str(diag["code"]), []).append(diag)
    assert {
        "CC902",
        "CC903",
        "CC905",
        "CC906",
        "CC907",
        "CC908",
        "CC909",
        "CC910",
    } <= set(by_code)
    assert len(by_code["CC906"]) == 2
    assert by_code["CC902"][0]["severity"] == "info"
    assert by_code["CC909"][0]["severity"] == "info"
    assert by_code["CC906"][0]["severity"] == "warning"


@then("test files remain exempt from public docstring and marker requirements")
def assert_test_exemptions(m4_state: dict[str, object]) -> None:
    diags = m4_state["diagnostics"]
    assert isinstance(diags, list)
    assert all("test_service.py" not in str(d["file"]) for d in diags)

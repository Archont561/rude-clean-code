"""BDD steps for deterministic Clean Code core rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from rude.core import discover_rules
from rude.core.types import Severity

EXPECTED_CODES = {
    "CC101",
    "CC102",
    "CC103",
    "CC104",
    "CC201",
    "CC202",
    "CC301",
    "CC302",
    "CC303",
}

BASIC_PROFILE_TOML = """
[tool.rude]
select = ["CC1", "CC2", "CC3"]
"""

scenarios(
    str(
        Path(__file__).resolve().parents[1] / "features" / "deterministic_rules.feature"
    )
)


@pytest.fixture
def cli_state(tmp_path: Path) -> dict[str, object]:
    return {"root": tmp_path}


@given("the rude-clean-code plugin is installed")
def plugin_is_installed() -> None:
    assert discover_rules(select=["CC"])


@when("Rude discovers plugin rules")
def discover_plugin_rules(cli_state: dict[str, object]) -> None:
    cli_state["cc_rules"] = discover_rules(select=["CC"])


@then("all nine deterministic CC rules are available with WARNING severity")
def all_nine_rules_available(cli_state: dict[str, object]) -> None:
    rules = cli_state["cc_rules"]
    assert isinstance(rules, list)
    assert {rule.code for rule in rules} == EXPECTED_CODES
    assert all(rule.severity == Severity.WARNING for rule in rules)


@then("selecting by CC, family prefix, or exact code filters the matching rules")
def select_filters_rules() -> None:
    assert {r.code for r in discover_rules(select=["CC1"])} == {
        "CC101",
        "CC102",
        "CC103",
        "CC104",
    }
    assert {r.code for r in discover_rules(select=["CC2"])} == {"CC201", "CC202"}
    assert {r.code for r in discover_rules(select=["CC3"])} == {
        "CC301",
        "CC302",
        "CC303",
    }
    assert [r.code for r in discover_rules(select=["CC302"])] == ["CC302"]


@given("a temporary project configured with the Basic profile")
def configure_basic_profile(cli_state: dict[str, object]) -> None:
    root = cli_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(BASIC_PROFILE_TOML, encoding="utf-8")


@given("a Python file violating deterministic CC rules and a clean nested function")
def write_violating_and_nested_clean_file(cli_state: dict[str, object]) -> None:
    root = cli_state["root"]
    assert isinstance(root, Path)
    source = """
def valid_outer(a, b, c, d, e):
    def inner():
        r1 = 1
        r2 = 2
        if a and b and c and d:
            return r1
        return r2
    return inner()


def overloaded(a, b, c, d, e, f):
    if a and b and c and d:
        return 1
    if a:
        return 2
    if b:
        return 3
    if c:
        return 4
    if d:
        return 5
    return 6
"""
    (root / "sample.py").write_text(source, encoding="utf-8")


@given(parsers.parse("a temporary project setting CC101 max_lines to {limit:d}"))
def configure_custom_cc101(cli_state: dict[str, object], limit: int) -> None:
    root = cli_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(
        f'[tool.rude]\nselect = ["CC101"]\n\n[tool.rude.rules.CC101]\nmax_lines = {limit}\n',
        encoding="utf-8",
    )


@given(parsers.parse("a Python function spanning {line_count:d} lines"))
def write_n_line_function(cli_state: dict[str, object], line_count: int) -> None:
    root = cli_state["root"]
    assert isinstance(root, Path)
    body = "\n".join("    x = 1" for _ in range(line_count - 1))
    (root / "sample.py").write_text(f"def sized():\n{body}\n", encoding="utf-8")


@when("Rude checks the temporary project")
def run_rude_on_temp_project(cli_state: dict[str, object]) -> None:
    root = cli_state["root"]
    assert isinstance(root, Path)
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
            str(root / "sample.py"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    cli_state["returncode"] = result.returncode
    cli_state["stderr"] = result.stderr
    cli_state["diagnostics"] = [
        json.loads(line) for line in result.stdout.splitlines() if line.strip()
    ]


@then(
    "diagnostics report measured value, configured limit, and suggested action as warnings"
)
def diagnostics_include_details_as_warnings(cli_state: dict[str, object]) -> None:
    diags = cli_state["diagnostics"]
    assert isinstance(diags, list)
    codes = {diag["code"] for diag in diags}
    assert {"CC102", "CC103", "CC302"} <= codes
    for diag in diags:
        assert diag["severity"] == "warning"
        assert ">" in diag["message"]
    assert all(diag["line"] != 2 for diag in diags)


@then("Rude exits successfully without treating warnings as errors")
def rude_exits_zero_for_warnings(cli_state: dict[str, object]) -> None:
    assert cli_state["returncode"] == 0, cli_state["stderr"]


@then(
    parsers.parse("Rude reports CC101 with measured {measured:d} and limit {limit:d}")
)
def rude_reports_configured_cc101(
    cli_state: dict[str, object], measured: int, limit: int
) -> None:
    diags = cli_state["diagnostics"]
    assert isinstance(diags, list)
    assert len(diags) == 1
    assert diags[0]["code"] == "CC101"
    assert f"{measured} > {limit}" in diags[0]["message"]


@when("Rude checks the package source directory with CC selected")
def run_rude_dogfood_on_package_src(cli_state: dict[str, object]) -> None:
    src_dir = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rude",
            "check",
            "--select",
            "CC",
            "--format",
            "json",
            str(src_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    cli_state["returncode"] = result.returncode
    cli_state["stderr"] = result.stderr
    cli_state["diagnostics"] = [
        json.loads(line) for line in result.stdout.splitlines() if line.strip()
    ]


@then("no CC diagnostics are emitted")
def no_cc_diagnostics_emitted(cli_state: dict[str, object]) -> None:
    assert cli_state["returncode"] == 0, cli_state["stderr"]
    assert cli_state["diagnostics"] == []

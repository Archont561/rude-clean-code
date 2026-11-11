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

EXPECTED_SEVERITIES: dict[str, Severity] = {
    "CC001": Severity.WARNING,
    "CC002": Severity.INFO,
    "CC003": Severity.WARNING,
    "CC004": Severity.WARNING,
    "CC005": Severity.WARNING,
    "CC101": Severity.WARNING,
    "CC102": Severity.WARNING,
    "CC103": Severity.WARNING,
    "CC104": Severity.WARNING,
    "CC105": Severity.INFO,
    "CC106": Severity.INFO,
    "CC107": Severity.WARNING,
    "CC108": Severity.INFO,
    "CC201": Severity.WARNING,
    "CC202": Severity.WARNING,
    "CC204": Severity.INFO,
    "CC205": Severity.INFO,
    "CC206": Severity.INFO,
    "CC207": Severity.WARNING,
    "CC301": Severity.WARNING,
    "CC302": Severity.WARNING,
    "CC303": Severity.WARNING,
    "CC304": Severity.INFO,
    "CC305": Severity.INFO,
    "CC306": Severity.WARNING,
    "CC307": Severity.INFO,
    "CC308": Severity.WARNING,
    "CC309": Severity.WARNING,
    "CC310": Severity.WARNING,
    "CC311": Severity.WARNING,
    "CC401": Severity.INFO,
    "CC402": Severity.INFO,
    "CC403": Severity.WARNING,
    "CC501": Severity.WARNING,
    "CC503": Severity.INFO,
    "CC504": Severity.WARNING,
    "CC601": Severity.INFO,
    "CC602": Severity.INFO,
    "CC603": Severity.INFO,
    "CC604": Severity.INFO,
    "CC605": Severity.INFO,
    "CC701": Severity.WARNING,
    "CC702": Severity.WARNING,
    "CC704": Severity.WARNING,
    "CC801": Severity.WARNING,
    "CC802": Severity.WARNING,
    "CC803": Severity.WARNING,
    "CC804": Severity.WARNING,
    "CC805": Severity.INFO,
    "CC901": Severity.WARNING,
    "CC902": Severity.INFO,
    "CC903": Severity.WARNING,
    "CC904": Severity.INFO,
    "CC905": Severity.WARNING,
    "CC906": Severity.WARNING,
    "CC907": Severity.WARNING,
    "CC908": Severity.WARNING,
    "CC909": Severity.INFO,
    "CC910": Severity.WARNING,
}

BASIC_PROFILE_TOML = """
[tool.rude]
select = ["CC1", "CC2", "CC3"]
ignore = ["CC105", "CC106", "CC108", "CC204", "CC205", "CC206", "CC304", "CC305", "CC307"]
"""

STRICT_PROFILE_TOML = """
[tool.rude]
select = ["CC0", "CC1", "CC2", "CC3", "CC4", "CC5", "CC6"]
"""

STRICT_SAMPLE_SOURCE = """
def do_stuff(item):
    temp: int = 42
    a = temp + 42
    b = a + 42
    if isinstance(item, int):
        return a
    if isinstance(item, float):
        return b
    if isinstance(item, str):
        return len(item)
    return 0


def copy_one(x):
    step1 = x + 10
    step2 = step1 * 2
    step3 = step2 - 3
    step4 = step3 + 4
    return step4


def copy_two(x):
    step1 = x + 10
    step2 = step1 * 2
    step3 = step2 - 3
    step4 = step3 + 4
    return step4
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


@then("all registered CC rules are available with their documented severities")
def all_rules_available(cli_state: dict[str, object]) -> None:
    rules = cli_state["cc_rules"]
    assert isinstance(rules, list)
    actual = {rule.code: rule.severity for rule in rules}
    assert actual == EXPECTED_SEVERITIES


EXPECTED_FAMILY_GROUPS: dict[str, set[str]] = {
    "CC0": {"CC001", "CC002", "CC003", "CC004", "CC005"},
    "CC1": {"CC101", "CC102", "CC103", "CC104", "CC105", "CC106", "CC107", "CC108"},
    "CC2": {"CC201", "CC202", "CC204", "CC205", "CC206", "CC207"},
    "CC3": {
        "CC301",
        "CC302",
        "CC303",
        "CC304",
        "CC305",
        "CC306",
        "CC307",
        "CC308",
        "CC309",
        "CC310",
        "CC311",
    },
    "CC4": {"CC401", "CC402", "CC403"},
    "CC5": {"CC501", "CC503", "CC504"},
    "CC6": {"CC601", "CC602", "CC603", "CC604", "CC605"},
    "CC7": {"CC701", "CC702", "CC704"},
    "CC8": {"CC801", "CC802", "CC803", "CC804", "CC805"},
    "CC9": {
        "CC901",
        "CC902",
        "CC903",
        "CC904",
        "CC905",
        "CC906",
        "CC907",
        "CC908",
        "CC909",
        "CC910",
    },
    "CC302": {"CC302"},
}


@then("selecting by CC, family prefix, or exact code filters the matching rules")
def select_filters_rules() -> None:
    for prefix, expected in EXPECTED_FAMILY_GROUPS.items():
        assert {r.code for r in discover_rules(select=[prefix])} == expected


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


@when("Rude checks the package source directory with the project Basic profile")
def run_rude_dogfood_on_package_src(cli_state: dict[str, object]) -> None:
    pkg_dir = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rude",
            "check",
            "--config",
            str(pkg_dir / "pyproject.toml"),
            "--format",
            "json",
            str(pkg_dir / "src"),
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


@given("a temporary project configured with the Strict profile")
def configure_strict_profile(cli_state: dict[str, object]) -> None:
    root = cli_state["root"]
    assert isinstance(root, Path)
    (root / "pyproject.toml").write_text(STRICT_PROFILE_TOML, encoding="utf-8")


@given("a Python file violating heuristic CC rules")
def write_strict_heuristic_sample(cli_state: dict[str, object]) -> None:
    root = cli_state["root"]
    assert isinstance(root, Path)
    (root / "sample.py").write_text(STRICT_SAMPLE_SOURCE, encoding="utf-8")


@then("Strict heuristic diagnostics carry expected severities and same-file guidance")
def verify_strict_heuristic_diagnostics(cli_state: dict[str, object]) -> None:
    diags = cli_state["diagnostics"]
    assert isinstance(diags, list)
    by_code = {diag["code"]: diag for diag in diags}
    assert {"CC401", "CC402", "CC403", "CC501", "CC601"} <= by_code.keys()
    assert by_code["CC401"]["severity"] == "info"
    assert by_code["CC402"]["severity"] == "info"
    assert by_code["CC601"]["severity"] == "info"
    assert by_code["CC403"]["severity"] == "warning"
    assert by_code["CC501"]["severity"] == "warning"
    assert "same-file" in by_code["CC501"]["message"].lower()

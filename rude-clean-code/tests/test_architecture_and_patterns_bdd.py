"""BDD steps for config-driven architecture and pattern boundary rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

FIXTURE_APP = Path(__file__).resolve().parent / "fixtures" / "consumer_app"

UNCONFIGURED_ARCH_TOML = """
[tool.rude]
select = ["CC7", "CC8"]
"""

CONFIGURED_ARCH_TOML = """
[tool.rude]
select = ["CC7", "CC8"]

[tool.rude.rules.CC701]
forbidden_modules = ["sqlalchemy", "boto3", "app_infra"]
only_paths = ["domain/"]

[tool.rude.rules.CC702]
concrete_classes = ["SqlOrderRepo"]
only_paths = ["domain/", "composition.py"]
exclude_paths = ["composition.py"]

[[tool.rude.rules.CC704.forbidden]]
from_paths = ["domain/"]
forbidden_modules = ["boto3"]

[tool.rude.rules.CC801]
data_modules = ["sqlalchemy"]
repository_paths = ["repositories/"]

[tool.rude.rules.CC802]
product_classes = ["StripeGateway"]
factory_paths = ["factories/"]
exclude_paths = ["composition.py"]

[tool.rude.rules.CC803]
strategy_base = "PaymentStrategy"
required_method = "pay"
strategy_paths = ["strategies/"]

[tool.rude.rules.CC804]
required_decorator = "register_handler"
handler_paths = ["handlers/"]

[tool.rude.rules.CC805]
service_classes = ["EmailNotifier"]
exclude_paths = ["composition.py"]
"""

scenarios(
    str(
        Path(__file__).resolve().parents[1]
        / "features"
        / "architecture_and_patterns.feature"
    )
)


@pytest.fixture
def arch_state(tmp_path: Path) -> dict[str, object]:
    return {"config": tmp_path / "pyproject.toml"}


@given(
    "a temporary configuration selecting the Architecture profile without rule options"
)
def write_unconfigured_arch_toml(arch_state: dict[str, object]) -> None:
    cfg = arch_state["config"]
    assert isinstance(cfg, Path)
    cfg.write_text(UNCONFIGURED_ARCH_TOML, encoding="utf-8")


@given("a temporary configuration declaring consumer modules, classes, and layer paths")
def write_configured_arch_toml(arch_state: dict[str, object]) -> None:
    cfg = arch_state["config"]
    assert isinstance(cfg, Path)
    cfg.write_text(CONFIGURED_ARCH_TOML, encoding="utf-8")


@when("Rude checks the consumer fixture tree")
def run_rude_on_fixture_tree(arch_state: dict[str, object]) -> None:
    cfg = arch_state["config"]
    assert isinstance(cfg, Path)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "rude",
            "check",
            "--config",
            str(cfg),
            "--format",
            "json",
            str(FIXTURE_APP),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    arch_state["returncode"] = proc.returncode
    arch_state["stderr"] = proc.stderr
    arch_state["diagnostics"] = [
        json.loads(line) for line in proc.stdout.splitlines() if line.strip()
    ]


@then("no architecture or pattern diagnostics are reported")
def assert_no_arch_diagnostics(arch_state: dict[str, object]) -> None:
    assert arch_state["returncode"] == 0, arch_state["stderr"]
    assert arch_state["diagnostics"] == []


@then("configured CC7xx and CC8xx diagnostics flag violations with expected severities")
def assert_expected_arch_diagnostics(arch_state: dict[str, object]) -> None:
    assert arch_state["returncode"] == 0, arch_state["stderr"]
    diags = arch_state["diagnostics"]
    assert isinstance(diags, list)
    codes = {d["code"] for d in diags}
    assert {
        "CC701",
        "CC702",
        "CC704",
        "CC801",
        "CC802",
        "CC803",
        "CC804",
        "CC805",
    } <= codes
    for diag in diags:
        expected_sev = "info" if diag["code"] == "CC805" else "warning"
        assert diag["severity"] == expected_sev


@then(
    "legitimate repository, factory, strategy, handler, and composition files stay clean"
)
def assert_clean_legitimate_files(arch_state: dict[str, object]) -> None:
    diags = arch_state["diagnostics"]
    assert isinstance(diags, list)
    flagged_files = {
        Path(d["file"]).resolve().relative_to(FIXTURE_APP.resolve()).as_posix()
        for d in diags
    }
    clean_files = {
        "domain/ports.py",
        "repositories/sql_order_repo.py",
        "factories/gateway_factory.py",
        "strategies/base.py",
        "strategies/card.py",
        "composition.py",
    }
    assert flagged_files.isdisjoint(clean_files)

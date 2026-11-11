"""Tests for config-driven dependency and boundary rules (CC701, CC702, CC704)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from rude.core import CheckOptions, Linter
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors, assert_no_fix

from rude_clean_code.rules.dependencies import (
    ConcreteInstantiationInDomain,
    ForbiddenConcreteImports,
    ForbiddenLayerDependency,
)

FIXTURE_APP = Path(__file__).resolve().parent / "fixtures" / "consumer_app"


def _run_rule_on_fixture(
    rule: object,
    root: Path = FIXTURE_APP,
) -> list[tuple[Path, object]]:
    linter = Linter()
    linter.register(rule)  # type: ignore[arg-type]
    return list(linter.check_paths_parallel([root]))


@pytest.mark.parametrize(
    "rule_cls",
    [
        ForbiddenConcreteImports,
        ConcreteInstantiationInDomain,
        ForbiddenLayerDependency,
    ],
)
def test_cc70x_rules_are_inert_when_unconfigured(rule_cls: type) -> None:
    rule = rule_cls()
    assert _run_rule_on_fixture(rule) == []
    assert_no_errors(
        rule_cls,
        "import sqlalchemy\nfrom sqlalchemy.orm import Session\nx = SqlOrderRepo()\n",
        filename="domain/order.py",
    )


def test_cc701_flags_import_and_from_import_submodule_matches() -> None:
    options = {
        "forbidden_modules": ["sqlalchemy", "boto3.s3", "app_infra"],
        "only_paths": ["domain/"],
    }
    source = (
        "import sqlalchemy\n"
        "import sqlalchemy.orm as orm, os\n"
        "import sqlalchemy_utils\n"
        "from sqlalchemy.orm import Session\n"
        "from boto3 import s3, client\n"
        "from app_infra.repos import SqlOrderRepo\n"
    )
    diags = assert_error_count(
        ForbiddenConcreteImports, source, 5, options=options, filename="domain/order.py"
    )
    assert all(d.code == "CC701" and d.severity == Severity.WARNING for d in diags)
    messages = "\n".join(d.message for d in diags)
    assert {"sqlalchemy.orm", "boto3.s3", "app_infra.repos"} <= {
        m for m in ("sqlalchemy.orm", "boto3.s3", "app_infra.repos") if m in messages
    }
    assert "sqlalchemy_utils" not in messages


def test_cc701_reports_no_autofix() -> None:
    assert_no_fix(
        ForbiddenConcreteImports,
        "from sqlalchemy.orm import Session\n",
        options={"forbidden_modules": ["sqlalchemy"], "only_paths": ["domain/"]},
        filename="domain/order.py",
    )


def test_cc701_real_file_tree_scoping_with_only_and_exclude_paths() -> None:
    rule = ForbiddenConcreteImports()
    rule.configure(
        {
            "forbidden_modules": ["sqlalchemy", "boto3", "app_infra"],
            "only_paths": ["domain/"],
            "exclude_paths": ["domain/ports.py"],
        }
    )
    results = _run_rule_on_fixture(rule)
    flagged_files = {path.relative_to(FIXTURE_APP).as_posix() for path, _ in results}
    assert flagged_files == {"domain/order.py"}
    assert len(results) == 5


def test_cc701_relative_import_requires_explicit_dot_prefix() -> None:
    assert_no_errors(
        ForbiddenConcreteImports,
        "from .repos import SqlOrderRepo\n",
        options={"forbidden_modules": ["repos"], "only_paths": ["domain/"]},
        filename="domain/order.py",
    )
    assert_error_count(
        ForbiddenConcreteImports,
        "from ..infra.db import Engine\n",
        1,
        options={"forbidden_modules": ["..infra"], "only_paths": ["domain/"]},
        filename="domain/order.py",
    )


def test_cc702_concrete_instantiation_in_domain_and_exclusions() -> None:
    options = {
        "concrete_classes": ["SqlOrderRepo", "billing.StripeGateway"],
        "only_paths": ["domain/"],
        "exclude_paths": ["composition.py", "domain/wiring.py"],
    }
    source = (
        "repo = SqlOrderRepo()\n"
        "qualified = app_infra.SqlOrderRepo()\n"
        "generic = SqlOrderRepo[int]()\n"
        "gw = billing.StripeGateway('k')\n"
        "ignored = self.SqlOrderRepo()\n"
        "other = StripeGateway('k')\n"
    )
    diags = assert_error_count(
        ConcreteInstantiationInDomain,
        source,
        4,
        options=options,
        filename="domain/order.py",
    )
    assert all(d.code == "CC702" and d.severity == Severity.WARNING for d in diags)
    assert_no_errors(
        ConcreteInstantiationInDomain,
        "repo = SqlOrderRepo()\n",
        options=options,
        filename="domain/wiring.py",
    )


def test_cc702_real_file_tree_flags_domain_and_skips_composition_root() -> None:
    rule = ConcreteInstantiationInDomain()
    rule.configure(
        {
            "concrete_classes": ["SqlOrderRepo"],
            "only_paths": ["domain/", "composition.py"],
            "exclude_paths": ["composition.py"],
        }
    )
    results = _run_rule_on_fixture(rule)
    flagged_files = {path.relative_to(FIXTURE_APP).as_posix() for path, _ in results}
    assert flagged_files == {"domain/order.py"}
    assert len(results) == 1


def test_cc704_general_layer_dependency_on_real_file_tree() -> None:
    rule = ForbiddenLayerDependency()
    rule.configure(
        {
            "forbidden": [
                {
                    "from_paths": ["domain/"],
                    "forbidden_modules": ["sqlalchemy", "boto3", "app_infra"],
                },
                ["services/", "sqlalchemy"],
            ]
        }
    )
    results = _run_rule_on_fixture(rule)
    by_file: dict[str, int] = {}
    for path, diag in results:
        assert diag.code == "CC704"  # type: ignore[attr-defined]
        assert diag.severity == Severity.WARNING  # type: ignore[attr-defined]
        rel = path.relative_to(FIXTURE_APP).as_posix()
        by_file[rel] = by_file.get(rel, 0) + 1
    assert by_file == {"domain/order.py": 5, "services/checkout_service.py": 1}


def test_cc704_toml_array_of_tables_via_cli(tmp_path: Path) -> None:
    config_path = tmp_path / "pyproject.toml"
    config_path.write_text(
        '[tool.rude]\nselect = ["CC704"]\n\n'
        "[[tool.rude.rules.CC704.forbidden]]\n"
        'from_paths = ["domain/"]\n'
        'forbidden_modules = ["sqlalchemy", "boto3", "app_infra"]\n',
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "rude",
            "check",
            "--config",
            str(config_path),
            "--format",
            "json",
            str(FIXTURE_APP),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    diags = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert len(diags) == 5
    assert all(d["code"] == "CC704" for d in diags)


def test_cc704_preserves_configuration_across_multiprocess_workers() -> None:
    rule = ForbiddenLayerDependency()
    rule.configure(
        {"forbidden": [["domain/", "sqlalchemy"], ["services/", "sqlalchemy"]]}
    )
    linter = Linter()
    linter.register(rule)
    results = list(linter.check_paths_parallel([FIXTURE_APP], CheckOptions(workers=2)))
    assert len(results) == 3


def test_cc701_relative_glob_only_paths_and_trailing_dot_prefix() -> None:
    rule = ForbiddenConcreteImports()
    rule.configure(
        {
            "forbidden_modules": ["sqlalchemy."],
            "only_paths": ["domain/*.py"],
        }
    )
    results = _run_rule_on_fixture(rule)
    assert len(results) == 1
    assert results[0][0].relative_to(FIXTURE_APP).as_posix() == "domain/order.py"


@pytest.mark.parametrize(
    ("rule_cls", "options"),
    [
        (ForbiddenConcreteImports, {"forbidden_modules": "sqlalchemy"}),
        (ForbiddenConcreteImports, {"only_paths": [123]}),
        (ForbiddenConcreteImports, {"exclude_paths": [None]}),
        (ConcreteInstantiationInDomain, {"concrete_classes": "SqlOrderRepo"}),
        (ConcreteInstantiationInDomain, {"only_paths": [False]}),
        (ForbiddenLayerDependency, {"forbidden": "invalid"}),
        (ForbiddenLayerDependency, {"forbidden": [["domain/"]]}),
        (ForbiddenLayerDependency, {"forbidden": [{"from_paths": []}]}),
        (
            ForbiddenLayerDependency,
            {
                "forbidden": [
                    {
                        "from_paths": ["domain/"],
                        "only_paths": ["domain/"],
                        "forbidden_modules": ["infra"],
                    }
                ]
            },
        ),
        (
            ForbiddenLayerDependency,
            {
                "forbidden": [
                    {
                        "from_paths": ["domain/"],
                        "forbidden_modules": ["infra"],
                        "unknown": True,
                    }
                ]
            },
        ),
    ],
)
def test_cc70x_invalid_options_raise_value_error(
    rule_cls: type, options: dict[str, object]
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError):
        rule.configure(options)

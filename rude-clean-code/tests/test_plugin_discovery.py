"""Tests for plugin entry-point discovery, selection, and configuration."""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import pytest
from rude.core import CheckOptions, Linter, discover_rules
from rude.core.node_types import VALID_NODE_TYPES
from rude.core.rule import Rule
from rude.core.types import Severity

from rude_clean_code._scope import ThresholdRule
from rude_clean_code.plugin import RULES

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


def test_entry_point_exposes_expected_rules() -> None:
    eps = [
        ep for ep in entry_points(group="rude.plugins") if ep.name == "rude_clean_code"
    ]
    assert len(eps) == 1
    plugin_module = eps[0].load()
    assert plugin_module.RULES == RULES
    assert {rule.code for rule in RULES} == EXPECTED_CODES


def test_every_registered_rule_satisfies_plugin_contract() -> None:
    for rule_cls in RULES:
        assert issubclass(rule_cls, Rule)
        assert rule_cls.severity == Severity.WARNING
        assert rule_cls.node_types is not None
        assert rule_cls.node_types <= VALID_NODE_TYPES
        assert rule_cls.message
        assert (rule_cls.__doc__ or "").strip()
        instance = rule_cls()
        assert instance.code == rule_cls.code


@pytest.mark.parametrize(
    ("select", "expected"),
    [
        (["CC"], EXPECTED_CODES),
        (["CC1"], {"CC101", "CC102", "CC103", "CC104"}),
        (["CC2"], {"CC201", "CC202"}),
        (["CC3"], {"CC301", "CC302", "CC303"}),
        (["CC101"], {"CC101"}),
        (["CC202", "CC302"], {"CC202", "CC302"}),
    ],
)
def test_rude_select_discovers_rules_by_prefix_and_code(
    select: list[str], expected: set[str]
) -> None:
    rules = discover_rules(select=select)
    assert {rule.code for rule in rules} == expected


def test_rude_ignore_excludes_specific_rule_from_cc_selection() -> None:
    rules = discover_rules(select=["CC"], ignore=["CC302"])
    assert {rule.code for rule in rules} == EXPECTED_CODES - {"CC302"}


def test_configured_rules_preserve_limits_under_multiprocess_checking(
    tmp_path: Path,
) -> None:
    for index in range(3):
        (tmp_path / f"sample_{index}.py").write_text(
            "def f():\n    a = 1\n    b = 2\n    return a + b\n",
            encoding="utf-8",
        )
    rules = discover_rules(select=["CC101"])
    rules[0].configure({"max_lines": 3})
    linter = Linter()
    linter.register_all(rules)

    results = list(
        linter.check_paths_parallel(
            [tmp_path],
            CheckOptions(workers=2),
        )
    )
    assert len(results) == 3
    assert all(diag.code == "CC101" and "4 > 3" in diag.message for _, diag in results)


@pytest.mark.parametrize("bad_value", [-1, True, False, "10", 3.5, None])
def test_threshold_rules_reject_invalid_option_values(bad_value: object) -> None:
    for rule_cls in RULES:
        rule = rule_cls()
        assert isinstance(rule, ThresholdRule)
        with pytest.raises(ValueError, match=rule.option_name):
            rule.configure({rule.option_name: bad_value})


def test_configure_empty_options_keeps_existing_limit() -> None:
    rule = discover_rules(select=["CC101"])[0]
    assert isinstance(rule, ThresholdRule)
    rule.configure({"max_lines": 12})
    rule.configure({})
    assert rule.limit == 12

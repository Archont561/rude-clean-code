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
EXPECTED_CODES = set(EXPECTED_SEVERITIES)


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
        assert rule_cls.severity == EXPECTED_SEVERITIES[rule_cls.code]
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
        (["CC0"], {"CC001", "CC002", "CC003", "CC004", "CC005"}),
        (
            ["CC1"],
            {"CC101", "CC102", "CC103", "CC104", "CC105", "CC106", "CC107", "CC108"},
        ),
        (
            ["CC2"],
            {"CC201", "CC202", "CC204", "CC205", "CC206", "CC207"},
        ),
        (
            ["CC3"],
            {
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
        ),
        (["CC4"], {"CC401", "CC402", "CC403"}),
        (["CC5"], {"CC501", "CC503", "CC504"}),
        (["CC6"], {"CC601", "CC602", "CC603", "CC604", "CC605"}),
        (["CC7"], {"CC701", "CC702", "CC704"}),
        (["CC8"], {"CC801", "CC802", "CC803", "CC804", "CC805"}),
        (
            ["CC9"],
            {
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
        ),
        (["CC101"], {"CC101"}),
        (["CC002", "CC202", "CC901"], {"CC002", "CC202", "CC901"}),
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
        if not isinstance(rule, ThresholdRule):
            continue
        with pytest.raises(ValueError, match=rule.option_name):
            rule.configure({rule.option_name: bad_value})


def test_configure_empty_options_keeps_existing_limit() -> None:
    rule = discover_rules(select=["CC101"])[0]
    assert isinstance(rule, ThresholdRule)
    rule.configure({"max_lines": 12})
    rule.configure({})
    assert rule.limit == 12

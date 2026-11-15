"""Tests for RCC-11 heuristics (CC106, CC108, CC307, CC604, CC605)."""

from __future__ import annotations

import pytest
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors

from rude_clean_code.rules.complexity_heuristics import InvertedConditional
from rude_clean_code.rules.coupling_heuristics import (
    ChainedAccess,
    ExternalPrivateAccess,
)
from rude_clean_code.rules.feature_envy import ExternalSameTypePairEnvy
from rude_clean_code.rules.function_heuristics import DataClump, UnusedParameter


def test_cc106_unused_parameter_exemptions() -> None:
    clean = (
        "from typing import Protocol, override\n\n"
        "class Repo(Protocol):\n"
        "    def save(self, order_id: str) -> None: ...\n\n"
        "class Child:\n"
        "    @override\n    def handle(self, event) -> None: return None\n\n"
        "def ok(used, _ignored, *args, **kwargs): return used\n"
        "def stub_pass(x): pass\n"
        "def stub_not_impl(x): raise NotImplementedError\n"
        "def closure_with_nonlocal(count):\n"
        "    def inc():\n        nonlocal count\n        count += 1\n        return count\n"
        "    return inc\n"
    )
    assert_no_errors(UnusedParameter, clean)
    assert_no_errors(
        UnusedParameter, "def bad(unused): return 1\n", filename="tests/test_sample.py"
    )


def test_cc106_unused_parameter_detection() -> None:
    diags = assert_error_count(
        UnusedParameter,
        "def compute(price, discount_unused):\n    return price\n",
        1,
    )
    assert diags[0].code == "CC106"
    assert diags[0].severity == Severity.INFO
    assert "discount_unused" in diags[0].message


def test_cc108_data_clump_in_signatures() -> None:
    clean = (
        "class Service:\n"
        "    def a(self, x, y): return x + y\n"
        "    def b(self, x, y): return x - y\n"
        "    def c(self, x, y): return x * y\n"
    )
    assert_no_errors(DataClump, clean)

    clump = (
        "class Endpoint:\n"
        "    def connect(self, host, port, timeout, tls=True): pass\n"
        "    def ping(self, host, port, timeout): pass\n"
        "    def close(self, host, port, timeout): pass\n"
    )
    diags = assert_error_count(DataClump, clump, 1)
    assert diags[0].code == "CC108"
    assert diags[0].severity == Severity.INFO
    assert "host" in diags[0].message
    assert "port" in diags[0].message
    assert "timeout" in diags[0].message


def test_cc307_inverted_conditional_exempts_guard_and_elif() -> None:
    clean = (
        "def guard(ok, item):\n"
        "    if not ok:\n        return None\n"
        "    if item is not None:\n        return item\n    else:\n        return 'default'\n\n"
        "def multi(a):\n"
        "    if a != 1:\n        return 'not one'\n"
        "    elif a == 2:\n        return 'two'\n"
        "    else:\n        return 'other'\n"
    )
    assert_no_errors(InvertedConditional, clean)

    violating = (
        "def choose(ready, mode):\n"
        "    if not ready:\n        x = 0\n    else:\n        x = 1\n"
        "    if mode != 'fast':\n        y = 2\n    else:\n        y = 3\n"
        "    return x + y\n"
    )
    diags = assert_error_count(InvertedConditional, violating, 2)
    assert all(d.code == "CC307" and d.severity == Severity.INFO for d in diags)


def test_cc604_chained_access_exemptions_and_thresholds() -> None:
    clean = (
        "class Svc:\n"
        "    def run(self, order, query):\n"
        "        a = self.ctx.path.parts.index('x')\n"
        "        b = order.customer.address.city\n"
        "        c = (\n"
        "            query.filter()\n            .order_by()\n            .limit()\n            .all()\n"
        "        )\n"
        "        return a, b, c\n"
    )
    assert_no_errors(ChainedAccess, clean)

    violating = "def wreck(order):\n    return order.customer.address.country.code\n"
    diags = assert_error_count(ChainedAccess, violating, 1)
    assert diags[0].code == "CC604"
    assert diags[0].severity == Severity.INFO
    assert "4 > 3" in diags[0].message
    assert_no_errors(
        ChainedAccess,
        "def f(a):\n    return a.b.c.d.e\n",
        options={"allowed_prefixes": ["a."]},
    )


def test_cc605_external_private_member_access_exemptions() -> None:
    clean = (
        "class Box:\n"
        "    def inspect(self, row):\n"
        "        return self._secret, cls_method(), super()._hook(), row._asdict(), row.__class__\n"
    )
    assert_no_errors(ExternalPrivateAccess, clean)
    assert_no_errors(
        ExternalPrivateAccess,
        "def f(fn, obj):\n"
        "    return fn.__name__, fn.__doc__, obj.__class__, fn.__code__\n",
    )
    assert_no_errors(
        ExternalPrivateAccess,
        "def f(obj):\n    return obj._internal\n",
        filename="tests/test_box.py",
    )

    violating = (
        "def peek(client):\n    client._token = 'x'\n    return client._session\n"
    )
    diags = assert_error_count(ExternalPrivateAccess, violating, 2)
    assert all(d.code == "CC605" and d.severity == Severity.INFO for d in diags)
    assert "_token" in diags[0].message


@pytest.mark.parametrize(
    ("rule_cls", "option", "bad_value"),
    [
        (UnusedParameter, "ignore_prefixes", "_"),
        (UnusedParameter, "exclude_tests", "yes"),
        (DataClump, "min_params", 1),
        (DataClump, "min_functions", 1),
        (ChainedAccess, "max_chain_depth", -1),
        (ChainedAccess, "allowed_prefixes", "self."),
        (ChainedAccess, "ignore_multiline", 1),
        (ExternalPrivateAccess, "exclude_tests", 0),
        (ExternalPrivateAccess, "allowed_members", "_asdict"),
    ],
)
def test_rcc11_invalid_options_raise_value_error(
    rule_cls: type, option: str, bad_value: object
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError, match=option):
        rule.configure({option: bad_value})


def test_cc605_flagged_dunders_escalation() -> None:
    source = "def f(fn):\n    return fn.__code__.co_filename\n"
    assert_no_errors(ExternalPrivateAccess, source)
    diags = assert_error_count(
        ExternalPrivateAccess, source, 1, options={"flagged_dunders": ["__code__"]}
    )
    assert diags[0].code == "CC605"
    assert diags[0].severity == Severity.INFO
    assert "__code__" in diags[0].message


def test_cc605_flagged_dunders_respects_receiver_and_allowed_members() -> None:
    assert_no_errors(
        ExternalPrivateAccess,
        "class Box:\n"
        "    def read(self):\n"
        "        return self.__dict__, super().__dict__\n",
        options={"flagged_dunders": ["__dict__"]},
    )
    assert_no_errors(
        ExternalPrivateAccess,
        "def f(obj):\n    return obj.__code__\n",
        options={"flagged_dunders": ["__code__"], "allowed_members": ["__code__"]},
    )
    assert_no_errors(
        ExternalPrivateAccess,
        "def f(obj):\n    return obj.__closure__\n",
        options={"flagged_dunders": ["__codes__"]},
    )


def test_cc606_flags_external_same_type_pair_helper() -> None:
    source = (
        "from tasknest.task import TaskDefinition\n"
        "\n"
        "def same(candidate: TaskDefinition, dep: TaskDefinition) -> bool:\n"
        "    return candidate.source_path == dep.source_path\n"
    )
    diags = assert_error_count(ExternalSameTypePairEnvy, source, 1)
    assert diags[0].code == "CC606"
    assert diags[0].severity == Severity.INFO
    assert "TaskDefinition" in diags[0].message
    assert "Feature Envy" in diags[0].message
    assert "violat" not in diags[0].message.lower()


def test_cc606_reports_the_issue_27_shape() -> None:
    source = (
        "from tasknest.task import TaskDefinition\n"
        "\n"
        "def _same_task(candidate: TaskDefinition, dep: TaskDefinition) -> bool:\n"
        "    if candidate is dep:\n"
        "        return True\n"
        "    if candidate.source_path is None or dep.source_path is None:\n"
        "        return False\n"
        "    return (\n"
        "        candidate.source_path.resolve() == dep.source_path.resolve()\n"
        "        and candidate.callable_fn.__code__.co_filename\n"
        "        == dep.callable_fn.__code__.co_filename\n"
        "    )\n"
    )
    diags = assert_error_count(ExternalSameTypePairEnvy, source, 1)
    assert "'candidate', 'dep'" in diags[0].message


def test_cc606_annotation_exemptions() -> None:
    clean = (
        "from pathlib import Path\n"
        "from typing import Any, Mapping, Sequence\n"
        "\n"
        "def strings(a: str, b: str) -> bool:\n"
        "    return a.isupper() or b.islower()\n"
        "\n"
        "def numbers(a: int, b: int) -> bool:\n"
        "    return a.bit_length() == b.bit_length()\n"
        "\n"
        "def paths(a: Path, b: Path) -> bool:\n"
        "    return a.parent == b.parent\n"
        "\n"
        "def mappings(a: Mapping, b: Mapping) -> bool:\n"
        "    return a.get('k') == b.get('k')\n"
        "\n"
        "def sequences(a: Sequence, b: Sequence) -> bool:\n"
        "    return a.index(0) == b.index(0)\n"
        "\n"
        "def anything(a: Any, b: Any) -> bool:\n"
        "    return a.value == b.value\n"
    )
    assert_no_errors(ExternalSameTypePairEnvy, clean)


def test_cc606_structural_exemptions() -> None:
    clean = (
        "from tasknest.task import TaskDefinition\n"
        "\n"
        "class TaskDefinition:\n"
        "    def __eq__(self, other: 'TaskDefinition') -> bool:\n"
        "        return self.source_path == other.source_path\n"
        "\n"
        "    def same(self, other: 'TaskDefinition') -> bool:\n"
        "        return self.source_path == other.source_path\n"
        "\n"
        "def passthrough(a: TaskDefinition, b: TaskDefinition) -> TaskDefinition:\n"
        "    return a\n"
        "\n"
        "def one_read(a: TaskDefinition, b: TaskDefinition) -> bool:\n"
        "    return a.source_path == b\n"
        "\n"
        "def different_types(a: TaskDefinition, b: OtherThing) -> bool:\n"
        "    return a.source_path == b.source_path\n"
    )
    assert_no_errors(ExternalSameTypePairEnvy, clean)
    assert_no_errors(
        ExternalSameTypePairEnvy,
        "def same(a: TaskDefinition, b: TaskDefinition) -> bool:\n"
        "    return a.source_path == b.source_path\n",
        filename="tests/test_tasknest.py",
    )


def test_cc606_configurable_options() -> None:
    source = (
        "def same(a: TaskDefinition, b: TaskDefinition) -> bool:\n"
        "    return a.source_path == b.source_path\n"
    )
    assert_no_errors(
        ExternalSameTypePairEnvy, source, options={"ignored_types": ["TaskDefinition"]}
    )
    assert_no_errors(
        ExternalSameTypePairEnvy, source, options={"min_attribute_reads": 3}
    )
    assert_error_count(
        ExternalSameTypePairEnvy,
        source,
        1,
        options={"exclude_tests": False},
        filename="tests/test_tasknest.py",
    )


def test_cc606_invalid_options_raise_value_error() -> None:
    rule = ExternalSameTypePairEnvy()
    with pytest.raises(ValueError, match="min_attribute_reads"):
        rule.configure({"min_attribute_reads": 1})
    with pytest.raises(ValueError, match="ignored_types"):
        rule.configure({"ignored_types": "TaskDefinition"})
    with pytest.raises(ValueError, match="exclude_tests"):
        rule.configure({"exclude_tests": "yes"})

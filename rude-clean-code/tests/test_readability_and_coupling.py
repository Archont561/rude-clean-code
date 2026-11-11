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

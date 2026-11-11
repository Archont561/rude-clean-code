"""Unit tests for CC401-CC403, CC501, and CC601 in-file heuristic rules."""

from __future__ import annotations

import pytest
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors

from rude_clean_code.rules.dry import DuplicateFunctionBody
from rude_clean_code.rules.heuristics import RepeatedTypeSwitch
from rude_clean_code.rules.naming import (
    RepeatedMagicLiteral,
    UnclearClassOrVariableName,
    UnclearFunctionName,
)

CC501_DUPLICATE_SAMPLE = (
    "def normalize_user(record):\n"
    "    # comment should not change normalization\n"
    "    cleaned = record.strip()\n"
    "    lowered = cleaned.lower()\n"
    "    parts = lowered.split(',')\n"
    "    filtered = [p for p in parts if p]\n"
    "    return '|'.join(filtered)\n\n"
    "def normalize_group(entry):\n"
    "    cleaned = entry.strip()\n"
    "    lowered = cleaned.lower()\n"
    "    parts = lowered.split(',')\n"
    "    filtered = [p for p in parts if p]\n"
    "    return '|'.join(filtered)\n"
)


def test_cc401_unclear_function_name_and_extendable_vague_list() -> None:
    clean = (
        "def compute_invoice_total(items):\n    return sum(items)\n"
        "def __repr__(self):\n    return 'x'\n"
        "def _(msg):\n    return msg\n"
    )
    assert_no_errors(UnclearFunctionName, clean)

    diags = assert_error_count(
        UnclearFunctionName,
        "def f(x):\n    return x\ndef process(payload):\n    return payload\n",
        2,
    )
    assert all(d.code == "CC401" and d.severity == Severity.INFO for d in diags)

    # Known false-positive shape: generic protocol method name 'handle' accepted at INFO.
    fp_diags = assert_error_count(
        UnclearFunctionName,
        "@overload\ndef handle(event):\n    return event\n",
        1,
    )
    assert fp_diags[0].severity == Severity.INFO

    # Extending vague_names adds custom words without shrinking built-in defaults.
    custom = "def process():\n    pass\ndef foo():\n    pass\n"
    assert_error_count(UnclearFunctionName, custom, 2, options={"vague_names": ["foo"]})


def test_cc402_unclear_class_and_variable_names_with_short_scope_exemption() -> None:
    clean = (
        "class OrderRepository:\n    pass\n"
        "def short_fn(items):\n"
        "    x: int = 0\n"
        "    for i in items:\n"
        "        x += i\n"
        "    return x\n"
    )
    assert_no_errors(UnclearClassOrVariableName, clean)

    violating = (
        "class C:\n    pass\n"
        "class Data:\n    pass\n"
        "data = {'k': 1}\n"
        "def long_fn(items):\n"
        "    x: int = 0\n"
        "    a = 1\n    b = 2\n    c = 3\n    d = 4\n"
        "    return x + a + b + c + d\n"
    )
    diags = assert_error_count(UnclearClassOrVariableName, violating, 4)
    assert all(d.code == "CC402" and d.severity == Severity.INFO for d in diags)

    # Known false-positive shape: single-letter TypeVar binding vs short-scope threshold.
    assert_error_count(
        UnclearClassOrVariableName,
        "def four_lines():\n    x: int = 1\n    y = x + 1\n    return y\n",
        1,
        options={"max_short_scope": 2},
    )


def test_cc402_accepts_extended_vague_names_without_shrinking_defaults() -> None:
    source = "data = 1\ncustom_bag = 2\n"
    assert_error_count(
        UnclearClassOrVariableName,
        source,
        2,
        options={"vague_names": ["custom_bag"]},
    )


def test_cc403_exempts_trivial_and_type_literals() -> None:
    clean = (
        '"""Docstring repeated.\n"""\n'
        "def ok():\n"
        '    """Repeated."""\n'
        "    a = [0, 0, 0, 1, 1, 1, -1, -1, -1]\n"
        '    b = ["", "", "", "only_twice", "only_twice"]\n'
        "    return a, b\n"
    )
    assert_no_errors(RepeatedMagicLiteral, clean)
    annotated = (
        "from typing import Literal, cast\n"
        "A = Literal['pending']\n"
        "B = Literal['pending']\n"
        "C = Literal['pending']\n"
        "def conv(v):\n"
        "    return [cast('Node', v), cast('Node', v), cast('Node', v)]\n"
    )
    assert_no_errors(RepeatedMagicLiteral, annotated)


def test_cc403_flags_repeated_magic_literals() -> None:
    violating = (
        "def bad():\n"
        "    t1 = 86400\n    t2 = 86400\n    t3 = 86400\n"
        "    s1 = 'retry_token'\n    s2 = 'retry_token'\n    s3 = 'retry_token'\n"
        "    return t1 + t2 + t3, s1 + s2 + s3\n"
    )
    diags = assert_error_count(RepeatedMagicLiteral, violating, 2)
    assert all(d.code == "CC403" and d.severity == Severity.WARNING for d in diags)
    assert "3" in diags[0].message


def test_cc403_handles_negative_literals_and_custom_min_occurrences() -> None:
    assert_no_errors(RepeatedMagicLiteral, "x = [-1, -1, -1, -1]\n")
    diags = assert_error_count(
        RepeatedMagicLiteral,
        "a = -42\nb = -42\n",
        1,
        options={"min_occurrences": 2},
    )
    assert "-42" in diags[0].message


def test_cc501_duplicate_function_body_states_same_file_limitation() -> None:
    short_pair = (
        "def first(x):\n    y = x + 1\n    return y\n"
        "def second(x):\n    y = x + 1\n    return y\n"
    )
    assert_no_errors(DuplicateFunctionBody, short_pair)

    source = CC501_DUPLICATE_SAMPLE.replace("entry", "record")
    diags = assert_error_count(DuplicateFunctionBody, source, 1)
    assert diags[0].code == "CC501"
    assert diags[0].severity == Severity.WARNING
    msg = diags[0].message.lower()
    assert "this" in msg and "file" in msg
    assert "normalize_user" in diags[0].message
    assert "line 1" in diags[0].message

    # Known false-positive shape: identical protocol/test stub bodies (< min_lines)
    # and distinct variable names stay silent.
    assert_no_errors(DuplicateFunctionBody, CC501_DUPLICATE_SAMPLE)


def test_cc501_custom_min_lines() -> None:
    pair = (
        "def alpha(x):\n    y = x + 1\n    return y * 2\n"
        "def beta(x):\n    y = x + 1\n    return y * 2\n"
    )
    diags = assert_error_count(DuplicateFunctionBody, pair, 1, options={"min_lines": 2})
    assert "2 >= 2" in diags[0].message


def test_cc601_clean_and_scope_isolation() -> None:
    clean = (
        "def convert(x, items):\n"
        "    if isinstance(x, int):\n        return x\n"
        "    if isinstance(x, str):\n        return len(x)\n"
        "    def inner(y):\n"
        "        if isinstance(y, int):\n            return 1\n"
        "        if isinstance(y, str):\n            return 2\n"
        "        return 0\n"
        "    if local_var == 'a':\n        return 1\n"
        "    elif local_var == 'b':\n        return 2\n"
        "    elif local_var == 'c':\n        return 3\n"
        "    return sum(items)\n"
    )
    assert_no_errors(RepeatedTypeSwitch, clean)


def test_cc601_flags_isinstance_and_attribute_chains() -> None:
    violating = (
        "def render(shape):\n"
        "    if isinstance(shape, Circle):\n        return 1\n"
        "    if isinstance(shape, Square):\n        return 2\n"
        "    if isinstance(shape, Triangle):\n        return 3\n"
        "    return 0\n"
        "def handle_event(event):\n"
        "    if event.kind == 'create':\n        return 1\n"
        "    elif event.kind == 'update':\n        return 2\n"
        "    elif event.kind == 'delete':\n        return 3\n"
        "    return 0\n"
    )
    diags = assert_error_count(RepeatedTypeSwitch, violating, 2)
    assert all(d.code == "CC601" and d.severity == Severity.INFO for d in diags)
    assert "polymorphism" in diags[0].message.lower()
    assert "event.kind" in diags[1].message


@pytest.mark.parametrize(
    ("rule_cls", "option", "bad_value"),
    [
        (UnclearFunctionName, "vague_names", "process"),
        (UnclearClassOrVariableName, "vague_names", 123),
        (UnclearClassOrVariableName, "max_short_scope", -1),
        (RepeatedMagicLiteral, "min_occurrences", 0),
        (RepeatedMagicLiteral, "min_occurrences", True),
        (DuplicateFunctionBody, "min_lines", -1),
        (RepeatedTypeSwitch, "min_isinstance", False),
    ],
)
def test_rcc3_invalid_options_raise_value_error(
    rule_cls: type, option: str, bad_value: object
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError, match=option):
        rule.configure({option: bad_value})

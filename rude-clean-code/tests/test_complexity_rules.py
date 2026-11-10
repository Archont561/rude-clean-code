"""Unit and property tests for CC301-CC303 complexity rules."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors, check_source

from rude_clean_code.rules.complexity import (
    ExcessiveBooleanOperands,
    ExcessiveBranching,
    ExcessiveNesting,
)

CC301_CLEAN = """
def f(items, mgr):
    if items:
        for item in items:
            with mgr() as ctx:
                try:
                    pass
                except ValueError:
                    pass
    elif len(items) == 0:
        match len(items):
            case 0:
                pass
    def inner():
        if True:
            if True:
                if True:
                    if True:
                        pass
"""

CC301_VIOLATING = """
def deep(items, mgr):
    if items:
        for item in items:
            async def nope():
                pass
            with mgr():
                while item:
                    try:
                        pass
                    except Exception:
                        pass
"""

CC303_CLEAN = """
def f(items, flag):
    if flag:
        pass
    elif not flag:
        pass
    else:
        pass
    for i in items:
        pass
    while False:
        pass
    x = 1 if flag else 2
    y = flag and True
    z = flag or False
    try:
        pass
    except RuntimeError:
        pass
    match x:
        case 1:
            pass
        case _:
            pass
    fn = lambda v: 1 if v else 2
    def inner():
        if True:
            pass
"""


def test_cc301_nesting_depth_across_control_structures_and_scopes() -> None:
    assert_no_errors(ExcessiveNesting, CC301_CLEAN)

    diags = assert_error_count(ExcessiveNesting, CC301_VIOLATING, 1)
    assert diags[0].code == "CC301"
    assert diags[0].severity == Severity.WARNING
    assert "5" in diags[0].message
    assert "4" in diags[0].message
    assert "extract" in diags[0].message.lower()

    assert_error_count(
        ExcessiveNesting,
        "def f(x):\n    if x:\n        pass\n",
        1,
        options={"max_depth": 0},
    )


def test_cc302_boolean_operands_outermost_and_inner_expressions() -> None:
    assert_no_errors(
        ExcessiveBooleanOperands,
        "ok = a and b and c\ngrouped = (a and b) or (c and d)\n",
    )
    flat = assert_error_count(
        ExcessiveBooleanOperands, "bad = a and b and c and d\n", 1
    )
    assert flat[0].code == "CC302"
    assert flat[0].severity == Severity.WARNING
    assert "4" in flat[0].message and "3" in flat[0].message
    assert "extract" in flat[0].message.lower()

    nested_inner = assert_error_count(
        ExcessiveBooleanOperands, "mixed = a and (b or c or d or e)\n", 1
    )
    assert "4 > 3" in nested_inner[0].message
    assert nested_inner[0].location.column == 15
    assert_error_count(ExcessiveBooleanOperands, "unparen = a and b or c and d\n", 1)
    assert_error_count(
        ExcessiveBooleanOperands, "two = a and b\n", 1, options={"max_operands": 1}
    )


def test_cc303_branching_decision_points_and_scope_isolation() -> None:
    # 9 own-scope decision points: if + elif + for + while + ternary + and + or + 2 cases
    assert_no_errors(ExcessiveBranching, CC303_CLEAN)

    violating = CC303_CLEAN.replace(
        "    while False:",
        "    if flag and True:\n        pass\n    while False:",
    )
    diags = assert_error_count(ExcessiveBranching, violating, 1)
    assert diags[0].code == "CC303"
    assert diags[0].severity == Severity.WARNING
    assert "11" in diags[0].message
    assert "10" in diags[0].message
    assert "decompose" in diags[0].message.lower()

    assert_error_count(
        ExcessiveBranching,
        "def f(a, b):\n    if a and b:\n        return 1\n    return 0\n",
        1,
        options={"max_branches": 1},
    )


def _nested_if_source(depth: int, inner_depth: int) -> str:
    lines = ["def outer(x):", "    def inner(y):"]
    if inner_depth == 0:
        lines.append("        pass")
    else:
        for level in range(inner_depth):
            lines.append("    " * (level + 2) + "if y:")
        lines.append("    " * (inner_depth + 2) + "pass")
    if depth == 0:
        lines.append("    pass")
    else:
        for level in range(depth):
            lines.append("    " * (level + 1) + "if x:")
        lines.append("    " * (depth + 1) + "pass")
    return "\n".join(lines) + "\n"


@settings(max_examples=40, deadline=None)
@given(
    depth=st.integers(min_value=0, max_value=8),
    inner_depth=st.integers(min_value=0, max_value=6),
    limit=st.integers(min_value=0, max_value=6),
)
def test_cc301_property_matches_own_scope_nesting_depth(
    depth: int, inner_depth: int, limit: int
) -> None:
    diags = check_source(
        ExcessiveNesting,
        _nested_if_source(depth, inner_depth),
        options={"max_depth": limit},
    )
    outer_diags = [d for d in diags if d.location.line == 1]
    assert len(outer_diags) == (1 if depth > limit else 0)
    if outer_diags:
        assert f"{depth} > {limit}" in outer_diags[0].message


@settings(max_examples=40, deadline=None)
@given(
    operand_count=st.integers(min_value=2, max_value=10),
    limit=st.integers(min_value=1, max_value=8),
)
def test_cc302_property_matches_boolean_operand_count(
    operand_count: int, limit: int
) -> None:
    expr = " and ".join(f"c{i}" for i in range(operand_count))
    diags = check_source(
        ExcessiveBooleanOperands,
        f"result = {expr}\n",
        options={"max_operands": limit},
    )
    assert len(diags) == (1 if operand_count > limit else 0)
    if diags:
        assert f"{operand_count} > {limit}" in diags[0].message


@settings(max_examples=40, deadline=None)
@given(
    branches=st.integers(min_value=0, max_value=14),
    nested_branches=st.integers(min_value=0, max_value=5),
    limit=st.integers(min_value=0, max_value=10),
)
def test_cc303_property_matches_own_scope_branches(
    branches: int, nested_branches: int, limit: int
) -> None:
    outer_ifs = "\n".join(f"    if x_{i}:\n        pass" for i in range(branches))
    inner_ifs = "\n".join(
        f"        if y_{i}:\n            pass" for i in range(nested_branches)
    )
    source = (
        "def outer():\n"
        "    def inner():\n"
        f"{inner_ifs or '        pass'}\n"
        "    fn = lambda v: 1 if v else 2\n"
        f"{outer_ifs or '    pass'}\n"
    )
    diags = check_source(
        ExcessiveBranching,
        source,
        options={"max_branches": limit},
    )
    outer_diags = [d for d in diags if d.location.line == 1]
    assert len(outer_diags) == (1 if branches > limit else 0)
    if outer_diags:
        assert f"{branches} > {limit}" in outer_diags[0].message

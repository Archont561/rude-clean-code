"""Unit and property tests for CC101-CC104 function rules."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors, check_source

from rude_clean_code.rules.functions import (
    FunctionTooLong,
    TooManyLocals,
    TooManyParameters,
    TooManyReturns,
)

CC103_CLEAN_WITH_NESTED = """
def outer(x):
    if x == 1:
        return 1
    if x == 2:
        return 2
    if x == 3:
        return 3
    if x == 4:
        return 4
    def inner(y):
        if y == 1:
            return 1
        if y == 2:
            return 2
        return 3
    return inner(x)
"""

CC103_VIOLATING = """
def many(x):
    if x == 1:
        return
    if x == 2:
        return 2
    if x == 3:
        return 3
    if x == 4:
        return 4
    if x == 5:
        return 5
    return 6
"""

CC104_WITH_LOCALS = """
g = 0
def outer(p1, p2):
    global g
    g = 1
    a = 1
    a = 2
    b: int = 3
    c = [k for k in range(3)]
    d = lambda z: z + 1
    for e in p1:
        pass
    with p2() as f:
        pass
    try:
        pass
    except Exception as err:
        pass
    if (h := 1):
        pass
    i = 9
    j = 10
    def inner():
        nonlocal a
        a = 99
        local_1 = 1
        local_2 = 2
        local_3 = 3
        return local_1
    return j
"""


def _assert_diagnostic_contract(
    message: str, *, measured: int, limit: int, action_hint: str
) -> None:
    assert str(measured) in message
    assert str(limit) in message
    assert action_hint in message.lower()


def _make_function_with_lines(total_lines: int, *, decorator: bool = False) -> str:
    prefix = "@dec\n" if decorator else ""
    if total_lines <= 1:
        return f"{prefix}def f(): pass\n"
    body = "\n".join("    x = 1" for _ in range(total_lines - 1))
    return f"{prefix}def f():\n{body}\n"


def test_cc101_clean_and_violating_with_decorators_and_custom_limit() -> None:
    assert_no_errors(FunctionTooLong, _make_function_with_lines(30, decorator=True))
    diags = assert_error_count(
        FunctionTooLong, _make_function_with_lines(31, decorator=True), 1
    )
    assert diags[0].code == "CC101"
    assert diags[0].severity == Severity.WARNING
    _assert_diagnostic_contract(
        diags[0].message, measured=31, limit=30, action_hint="extract"
    )
    configured = assert_error_count(
        FunctionTooLong,
        "def short():\n    a = 1\n    return a\n",
        1,
        options={"max_lines": 2},
    )
    _assert_diagnostic_contract(
        configured[0].message, measured=3, limit=2, action_hint="extract"
    )


def test_cc102_parameters_include_self_splats_and_exclude_separators() -> None:
    clean = "def method(self, a, /, b: int = 1, *, c=2, **kwargs):\n    return a\n"
    assert_no_errors(TooManyParameters, clean)
    type_params_only = (
        "def typed_fn[T, U](a: T, b: U, c: int = 1, d: int = 2, e: int = 3) -> T:\n"
        "    return a\n"
    )
    assert_no_errors(TooManyParameters, type_params_only)

    violating = (
        "def method(self, a, /, b: int = 1, *, c=2, *args, **kwargs):\n    return a\n"
    )
    diags = assert_error_count(TooManyParameters, violating, 1)
    assert diags[0].code == "CC102"
    assert diags[0].severity == Severity.WARNING
    _assert_diagnostic_contract(
        diags[0].message, measured=6, limit=5, action_hint="group"
    )
    assert_error_count(
        TooManyParameters,
        "def f(a, b, c): return a\n",
        1,
        options={"max_parameters": 2},
    )


def test_cc103_counts_own_scope_returns_only() -> None:
    assert_no_errors(TooManyReturns, CC103_CLEAN_WITH_NESTED)

    diags = assert_error_count(TooManyReturns, CC103_VIOLATING, 1)
    assert diags[0].code == "CC103"
    assert diags[0].severity == Severity.WARNING
    _assert_diagnostic_contract(
        diags[0].message, measured=6, limit=5, action_hint="simplify"
    )

    assert_error_count(
        TooManyReturns,
        "def f(x):\n    if x:\n        return 1\n    return 2\n",
        1,
        options={"max_returns": 1},
    )


def test_cc104_counts_scope_locals_only() -> None:
    clean = CC104_WITH_LOCALS.replace("    j = 10\n", "").replace(
        "return j", "return i"
    )
    assert_no_errors(TooManyLocals, clean)

    diags = assert_error_count(TooManyLocals, CC104_WITH_LOCALS, 1)
    assert diags[0].code == "CC104"
    assert diags[0].severity == Severity.WARNING
    _assert_diagnostic_contract(
        diags[0].message, measured=11, limit=10, action_hint="split"
    )

    assert_error_count(
        TooManyLocals,
        "def f():\n    x = 1\n    y = 2\n    return x + y\n",
        1,
        options={"max_locals": 1},
    )


@settings(max_examples=50, deadline=None)
@given(
    line_count=st.integers(min_value=1, max_value=30),
    limit=st.integers(min_value=1, max_value=20),
)
def test_cc101_property_matches_line_threshold(line_count: int, limit: int) -> None:
    diags = check_source(
        FunctionTooLong,
        _make_function_with_lines(line_count),
        options={"max_lines": limit},
    )
    assert len(diags) == (1 if line_count > limit else 0)
    if diags:
        assert f"{line_count} > {limit}" in diags[0].message


@settings(max_examples=50, deadline=None)
@given(
    param_count=st.integers(min_value=0, max_value=12),
    limit=st.integers(min_value=0, max_value=10),
)
def test_cc102_property_matches_parameter_threshold(
    param_count: int, limit: int
) -> None:
    params = ", ".join(f"p{i}" for i in range(param_count))
    diags = check_source(
        TooManyParameters,
        f"def f({params}):\n    return None\n",
        options={"max_parameters": limit},
    )
    assert len(diags) == (1 if param_count > limit else 0)
    if diags:
        assert f"{param_count} > {limit}" in diags[0].message


@settings(max_examples=50, deadline=None)
@given(
    return_count=st.integers(min_value=0, max_value=12),
    nested_returns=st.integers(min_value=0, max_value=4),
    limit=st.integers(min_value=0, max_value=10),
)
def test_cc103_property_matches_own_scope_returns(
    return_count: int, nested_returns: int, limit: int
) -> None:
    outer_branches = "\n".join(
        f"    if flag_{i}:\n        return {i}" for i in range(return_count)
    )
    inner_branches = "\n".join(
        f"        if inner_{i}:\n            return {i}" for i in range(nested_returns)
    )
    source = (
        "def outer():\n"
        "    def inner():\n"
        f"{inner_branches or '        pass'}\n"
        f"{outer_branches or '    pass'}\n"
    )
    diags = check_source(TooManyReturns, source, options={"max_returns": limit})
    outer_diags = [d for d in diags if d.location.line == 1]
    assert len(outer_diags) == (1 if return_count > limit else 0)
    if outer_diags:
        assert f"{return_count} > {limit}" in outer_diags[0].message


@settings(max_examples=50, deadline=None)
@given(
    local_count=st.integers(min_value=0, max_value=15),
    nested_locals=st.integers(min_value=0, max_value=5),
    limit=st.integers(min_value=0, max_value=12),
)
def test_cc104_property_matches_own_scope_locals(
    local_count: int, nested_locals: int, limit: int
) -> None:
    assigns = "\n".join(f"    var_{i} = {i}" for i in range(local_count))
    nested_assigns = "\n".join(f"        nvar_{i} = {i}" for i in range(nested_locals))
    source = (
        "def outer(arg_a, arg_b):\n"
        f"{assigns}\n"
        "    def inner():\n"
        f"{nested_assigns or '        pass'}\n"
    )
    expected_locals = local_count + 1  # includes local binding for `inner`
    diags = check_source(TooManyLocals, source, options={"max_locals": limit})
    outer_diags = [d for d in diags if d.location.line == 1]
    assert len(outer_diags) == (1 if expected_locals > limit else 0)
    if outer_diags:
        assert f"{expected_locals} > {limit}" in outer_diags[0].message

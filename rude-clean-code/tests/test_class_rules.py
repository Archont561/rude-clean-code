"""Unit and property tests for CC201-CC202 class rules."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors, check_source

from rude_clean_code.rules.classes import ClassTooLarge, TooManyMethods


def _make_class_with_lines(total_lines: int, *, decorator: bool = False) -> str:
    prefix = "@dataclass\n" if decorator else ""
    if total_lines <= 1:
        return f"{prefix}class C: pass\n"
    body = "\n".join(f"    attr_{i} = {i}" for i in range(total_lines - 1))
    return f"{prefix}class C:\n{body}\n"


def _make_class_with_methods(regular: int, dunder: int) -> str:
    lines = ["class C:"]
    if regular == 0 and dunder == 0:
        lines.append("    pass")
    for idx in range(dunder):
        lines.append(f"    def __dunder_{idx}__(self):")
        lines.append("        return 0")
    for idx in range(regular):
        if idx % 2 == 1:
            lines.append("    @property")
        lines.append(f"    def method_{idx}(self):")
        lines.append("        def helper():")
        lines.append("            return 1")
        lines.append("        return helper()")
    lines.append("    class Inner:")
    lines.append("        def inner_method(self):")
    lines.append("            return 2")
    return "\n".join(lines) + "\n"


def test_cc201_class_span_clean_and_violating() -> None:
    assert_no_errors(ClassTooLarge, _make_class_with_lines(200, decorator=True))
    diags = assert_error_count(
        ClassTooLarge, _make_class_with_lines(201, decorator=True), 1
    )
    assert diags[0].code == "CC201"
    assert diags[0].severity == Severity.WARNING
    assert "201" in diags[0].message
    assert "200" in diags[0].message
    assert "extract" in diags[0].message.lower()

    assert_error_count(
        ClassTooLarge,
        _make_class_with_lines(5),
        1,
        options={"max_lines": 4},
    )


def test_cc202_counts_direct_methods_and_reports_dunders() -> None:
    assert_no_errors(TooManyMethods, _make_class_with_methods(regular=12, dunder=3))

    diags = assert_error_count(
        TooManyMethods, _make_class_with_methods(regular=13, dunder=3), 1
    )
    assert diags[0].code == "CC202"
    assert diags[0].severity == Severity.WARNING
    msg = diags[0].message
    assert "16" in msg
    assert "15" in msg
    assert "3 dunder" in msg
    assert "extract" in msg.lower()

    assert_error_count(
        TooManyMethods,
        "class S:\n    async def run(self):\n        return 1\n    def b(self):\n        return 2\n",
        1,
        options={"max_methods": 1},
    )


@settings(max_examples=40, deadline=None)
@given(
    line_count=st.integers(min_value=2, max_value=30),
    limit=st.integers(min_value=1, max_value=25),
)
def test_cc201_property_matches_class_line_threshold(
    line_count: int, limit: int
) -> None:
    diags = check_source(
        ClassTooLarge,
        _make_class_with_lines(line_count),
        options={"max_lines": limit},
    )
    assert len(diags) == (1 if line_count > limit else 0)
    if diags:
        assert f"{line_count} > {limit}" in diags[0].message


@settings(max_examples=40, deadline=None)
@given(
    regular=st.integers(min_value=0, max_value=10),
    dunder=st.integers(min_value=0, max_value=5),
    limit=st.integers(min_value=0, max_value=12),
)
def test_cc202_property_matches_method_threshold(
    regular: int, dunder: int, limit: int
) -> None:
    total = regular + dunder
    diags = check_source(
        TooManyMethods,
        _make_class_with_methods(regular=regular, dunder=dunder),
        options={"max_methods": limit},
    )
    outer_diags = [d for d in diags if d.location.line == 1]
    assert len(outer_diags) == (1 if total > limit else 0)
    if outer_diags:
        assert f"{total} > {limit}" in outer_diags[0].message
        assert f"{dunder} dunder" in outer_diags[0].message

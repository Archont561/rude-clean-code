"""Tests for RCC-7 and RCC-12 documentation and comment rules (CC901-CC910)."""

from __future__ import annotations

import pytest
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors

from rude_clean_code.rules.comments import (
    BlanketOrUnexplainedSuppression,
    CommentedOutCode,
    CommentRestatingCode,
    EmptyTodoComment,
    TodoWithoutReference,
)
from rude_clean_code.rules.documentation import (
    DanglingStringLiteral,
    DocstringParameterDrift,
    DocstringReturnYieldMismatch,
    EmptyDocstring,
    MissingDocstring,
)


def test_cc901_public_api_missing_docstring_exemptions() -> None:
    clean = (
        '"""Public module docstring."""\n\n'
        "class _PrivateClass:\n    def hidden(self): return 1\n\n"
        "class PublicClass:\n"
        '    """Public class docstring."""\n\n'
        "    def __init__(self, x): self.x = x\n"
        "    @property\n    def value(self):\n"
        '        """Value getter."""\n        return self.x\n'
        "    @value.setter\n    def value(self, v): self.x = v\n\n"
        "def public_fn():\n"
        '    """Public function docstring."""\n'
        "    def local_helper(): return 1\n"
        "    return local_helper()\n\n"
        "def _private_helper(): return 2\n"
    )
    assert_no_errors(MissingDocstring, clean)
    assert_no_errors(MissingDocstring, "def f(): pass\n", filename="tests/test_api.py")


def test_cc901_flags_missing_public_docstrings() -> None:
    missing = "class Widget:\n    def render(self):\n        return 'ok'\n"
    diags = assert_error_count(MissingDocstring, missing, 3)
    assert all(d.code == "CC901" and d.severity == Severity.WARNING for d in diags)


def test_cc902_commented_out_code_is_conservative_on_prose_and_directives() -> None:
    clean = (
        "#! /usr/bin/env python3\n"
        "# -*- coding: utf-8 -*-\n"
        "# noqa: E501\n"
        "# type: ignore[attr-defined]\n"
        "# See process(data) for normalization steps.\n"
        "# Call validate(order) before persisting.\n"
        "# Status: ready\n"
        "# >>> foo(1)\n"
        "def ok():\n"
        "    return 1  # single line comment\n"
    )
    assert_no_errors(CommentedOutCode, clean)

    commented_code = (
        "def process(items):\n"
        "    # old_total = sum(items)\n"
        "    # if old_total > 0:\n"
        "    #     return old_total * 2\n"
        "    return len(items)\n"
    )
    diags = assert_error_count(CommentedOutCode, commented_code, 1)
    assert diags[0].code == "CC902"
    assert diags[0].severity == Severity.INFO


def test_cc903_clean_and_test_exempted_markers() -> None:
    clean = (
        "# TODO(#42): extract helper after migration\n"
        "# FIXME(PROJ-123): handle timeout cleanly\n"
        "# XXX https://github.com/org/repo/issues/9 legacy fallback\n"
        "# TODO(@alice until 2026-12-01): remove compat shim\n"
        "# Note: nothing todo here in lowercase prose.\n"
    )
    assert_no_errors(
        TodoWithoutReference,
        clean,
        options={
            "expiry_pattern": r"until\s+(\d{4}-\d{2}-\d{2})",
            "reference_date": "2026-11-11",
        },
    )
    assert_no_errors(
        TodoWithoutReference,
        "# TODO: okay inside test\n# NOCOMMIT: test fixture\n",
        options={"forbidden_markers": ["NOCOMMIT"]},
        filename="tests/test_notes.py",
    )


def test_cc903_flags_missing_reference_expired_and_forbidden_markers() -> None:
    violating = (
        "# TODO: missing ticket reference\n"
        "# HACK: tracked hack keyword lacking reference\n"
        "# TODO(#55 until 2025-01-15): expired deadline\n"
        "# NOCOMMIT remove debug hook\n"
    )
    diags = assert_error_count(
        TodoWithoutReference,
        violating,
        4,
        options={
            "keywords": ["TODO", "FIXME", "XXX", "HACK"],
            "expiry_pattern": r"until\s+(\d{4}-\d{2}-\d{2})",
            "reference_date": "2026-11-11",
            "forbidden_markers": ["NOCOMMIT"],
        },
    )
    assert all(d.code == "CC903" and d.severity == Severity.WARNING for d in diags)


def test_cc904_comment_restating_code_experimental() -> None:
    clean = (
        "def run(items):\n"
        "    # Guard against empty batches to avoid division by zero downstream\n"
        "    if not items:\n        return 0\n"
        "    # Aggregate daily revenue totals\n"
        "    count = len(items)\n    return count\n"
    )
    assert_no_errors(CommentRestatingCode, clean)

    restating = "def run_cfg(path):\n    # Load config\n    config = load_config(path)\n    return config\n"
    diags = assert_error_count(CommentRestatingCode, restating, 1)
    assert diags[0].code == "CC904"
    assert diags[0].severity == Severity.INFO
    assert "experimental" in diags[0].message.lower()
    assert_error_count(
        CommentRestatingCode,
        "def bump(counter):\n    # increment counter\n    counter += 1\n    return counter\n",
        1,
        options={"max_overlap": 0.5},
    )


def test_cc905_empty_or_descriptionless_todo() -> None:
    clean = (
        "# TODO(#12): migrate parser to streaming iterator\n# FIXME: add retry jitter\n"
    )
    assert_no_errors(EmptyTodoComment, clean)

    empty = "# TODO\n# TODO:\n# TODO(JIRA-123):\n# FIXME: x\n"
    diags = assert_error_count(EmptyTodoComment, empty, 4)
    assert all(d.code == "CC905" and d.severity == Severity.WARNING for d in diags)


def test_cc906_blanket_and_unexplained_suppressions() -> None:
    clean = (
        "# Keep prose mentioning noqa comments untouched\n"
        "x = 1  # noqa: E501\n"
        "y = 2  # type: ignore[assignment]\n"
        "z = 3  # noqa: CC601 -- AST dispatcher requires explicit type checks\n"
    )
    assert_no_errors(
        BlanketOrUnexplainedSuppression, clean, options={"require_reason_for": ["CC6"]}
    )

    bad = "a = 1  # noqa\nb = 2  # type: ignore\nc = 3  # noqa: CC601\n"
    diags = assert_error_count(
        BlanketOrUnexplainedSuppression, bad, 3, options={"require_reason_for": ["CC6"]}
    )
    assert all(d.code == "CC906" and d.severity == Severity.WARNING for d in diags)


def test_cc907_empty_or_placeholder_docstring() -> None:
    clean = '"""Real module documentation."""\n\ndef compute():\n    """Summary."""\n    return 1\n'
    assert_no_errors(EmptyDocstring, clean)

    placeholders = (
        '"""   """\n\nclass Placeholder:\n    """..."""\n\n'
        '    def run(self):\n        """TODO: document run."""\n        return None\n'
    )
    diags = assert_error_count(EmptyDocstring, placeholders, 3)
    assert all(d.code == "CC907" and d.severity == Severity.WARNING for d in diags)


def test_cc908_docstring_parameter_drift_clean_variadics_and_styles() -> None:
    clean = (
        "def google_ok(alpha: int, beta: str = 'x', *names: str, **markup: bool) -> str:\n"
        '    """Run operation.\n\n'
        "    Args:\n        alpha (int): First value.\n        beta: Optional label.\n"
        '        *names: Module names.\n        erase: Optional forwarded flag.\n    """\n'
        "    return beta\n\n"
        "def sphinx_ok(count: int) -> int:\n"
        '    """Count items.\n\n    :param int count: Number of entries.\n    """\n'
        "    return count\n"
    )
    assert_no_errors(DocstringParameterDrift, clean, options={"report_missing": True})


def test_cc908_docstring_parameter_drift_reports_phantom_and_missing() -> None:
    phantom = (
        "def google_bad(alpha: int, undocumented: str) -> int:\n"
        '    """Process alpha.\n\n'
        "    Args:\n        alpha: Present value.\n        ghost: Removed earlier.\n"
        '    """\n'
        "    return alpha\n"
    )
    assert_error_count(DocstringParameterDrift, phantom, 1)
    assert_error_count(
        DocstringParameterDrift, phantom, 2, options={"report_missing": True}
    )


def test_cc909_docstring_return_or_yield_exemptions() -> None:
    clean = (
        "from abc import ABC, abstractmethod\n\n"
        "class Repo(ABC):\n"
        "    @abstractmethod\n    def get(self, key: str) -> str:\n"
        '        """Load item.\n\n        Returns:\n            Stored string.\n        """\n'
        "        ...\n"
        "    def start_error(self) -> BaseException | None:\n"
        '        """:returns: startup failure if any, else None."""\n'
        "        return None\n\n"
        "def gen(items):\n"
        '    """Yield values.\n\n    Yields:\n        Each item.\n    """\n'
        "    yield from items\n"
    )
    assert_no_errors(DocstringReturnYieldMismatch, clean)


def test_cc909_docstring_return_or_yield_mismatch() -> None:
    mismatched = (
        "def stream_bad(items):\n"
        '    """Stream items.\n\n    Returns:\n        Items.\n    """\n'
        "    for item in items:\n        yield item\n\n"
        "def void_bad(x: list[int]) -> None:\n"
        '    """Append zero.\n\n    Returns:\n        Nothing.\n    """\n'
        "    x.append(0)\n"
    )
    diags = assert_error_count(DocstringReturnYieldMismatch, mismatched, 2)
    assert all(d.code == "CC909" and d.severity == Severity.INFO for d in diags)


def test_cc910_dangling_string_literal_exempts_attribute_docs_including_try_init() -> (
    None
):
    clean = (
        '"""Module docstring."""\n\nAPI_VERSION = "v1"\n"""Module constant doc."""\n\n'
        "class Config:\n"
        '    """Class docstring."""\n\n    timeout: int = 30\n    """Class field doc."""\n\n'
        "    def __init__(self, ret) -> None:\n"
        '        """Constructor docstring."""\n'
        "        try:\n            self.ret = int(ret)\n"
        '            """Parsed return code inside try block."""\n'
        "        except ValueError:\n            self.ret = 0\n"
    )
    assert_no_errors(DanglingStringLiteral, clean)


def test_cc910_dangling_string_literal_flags_stray_body_strings() -> None:
    dangling = (
        '"""Module docstring."""\n\n'
        '"""Stray module string after docstring."""\n\n'
        "def work() -> int:\n"
        '    """Function docstring."""\n'
        '    x = 1\n    "stray comment literal inside function"\n    return x\n'
    )
    diags = assert_error_count(DanglingStringLiteral, dangling, 2)
    assert all(d.code == "CC910" and d.severity == Severity.WARNING for d in diags)


@pytest.mark.parametrize(
    ("rule_cls", "option", "bad_value"),
    [
        (MissingDocstring, "check_modules", "yes"),
        (MissingDocstring, "check_classes", 1),
        (CommentedOutCode, "min_lines", 0),
        (TodoWithoutReference, "reference_pattern", "["),
        (TodoWithoutReference, "keywords", "TODO"),
        (TodoWithoutReference, "expiry_pattern", "["),
        (TodoWithoutReference, "reference_date", "not-a-date"),
        (TodoWithoutReference, "forbidden_markers", "NOCOMMIT"),
        (TodoWithoutReference, "exclude_tests", 1),
        (CommentRestatingCode, "max_overlap", 1.5),
        (EmptyTodoComment, "keywords", 123),
        (EmptyTodoComment, "min_description_chars", -1),
        (BlanketOrUnexplainedSuppression, "require_reason_for", "CC6"),
        (EmptyDocstring, "check_modules", 0),
        (DocstringParameterDrift, "report_missing", "false"),
    ],
)
def test_rcc7_and_rcc12_invalid_options_raise_value_error(
    rule_cls: type, option: str, bad_value: object
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError, match=option):
        rule.configure({option: bad_value})

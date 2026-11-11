"""Unit tests for CC107, CC207, CC306, and CC308-CC311 structural/fail-fast rules."""

from __future__ import annotations

import pytest
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors

from rude_clean_code.rules.classes import TooManyBaseClasses
from rude_clean_code.rules.complexity import GlobalStatement, NestedTernary
from rude_clean_code.rules.errors import (
    BroadExceptionSwallowed,
    MissingExceptionChaining,
    OversizedTryBlock,
)
from rude_clean_code.rules.functions import UnusedPrivateHelper

CC309_CLEAN_SAMPLE = (
    "import contextlib\n"
    "def ok(fn, log):\n"
    "    with contextlib.suppress(Exception):\n"
    "        fn()\n"
    "    try:\n"
    "        fn()\n"
    "    except ValueError:\n"
    "        pass\n"
    "    except Exception as err:\n"
    "        log.warning('failed: %s', err)\n"
    "        return None\n"
    "    except BaseException:\n"
    "        raise\n"
)

CC309_VIOLATING_SAMPLE = (
    "def bad(fn):\n"
    "    try:\n        fn()\n    except:\n        pass\n"
    "    try:\n        fn()\n    except Exception:\n        ...\n"
    "    try:\n        fn()\n    except BaseException:\n        return None\n"
    "    for _ in range(2):\n"
    "        try:\n            fn()\n        except (TypeError, Exception):\n            continue\n"
    "    try:\n        fn()\n    except* Exception:\n        return []\n"
)

CC310_CLEAN_SAMPLE = (
    "def parse_data(raw):\n"
    "    try:\n"
    "        return int(raw)\n"
    "    except ValueError as exc:\n"
    "        raise RuntimeError('bad') from exc\n"
    "    except TypeError:\n"
    "        raise RuntimeError('masked') from None\n"
    "    except KeyError:\n"
    "        raise\n"
    "    else:\n"
    "        raise RuntimeError('outside except')\n"
    "    finally:\n"
    "        raise RuntimeError('cleanup')\n"
    "def outer():\n"
    "    try:\n"
    "        pass\n"
    "    except RuntimeError:\n"
    "        def helper():\n"
    "            raise ValueError('nested fn scope')\n"
    "        return helper\n"
)


def test_cc107_flags_unused_private_helpers_and_respects_exemptions() -> None:
    source = (
        "def _used_helper():\n"
        "    return 1\n"
        "def public_api():\n"
        "    return _used_helper()\n"
        "def __dunder_hook__():\n"
        "    return 2\n"
        "@pytest.fixture\n"
        "def _ignored_fixture():\n"
        "    return 3\n"
        "def _dead_helper():\n"
        "    return 4\n"
        "class _DeadClass:\n"
        "    pass\n"
    )
    diags = assert_error_count(
        UnusedPrivateHelper,
        source,
        2,
        options={"ignore_decorators": ["pytest.fixture"]},
    )
    assert all(d.code == "CC107" and d.severity == Severity.WARNING for d in diags)
    messages = {d.message for d in diags}
    assert any("_dead_helper" in msg for msg in messages)
    assert any("_DeadClass" in msg for msg in messages)


def test_cc107_ignores_nested_privates_and_matches_short_decorator_name() -> None:
    clean = (
        "import functools\n"
        "def outer():\n"
        "    def _nested_unused():\n"
        "        return 1\n"
        "    return 2\n"
        "@functools.lru_cache\n"
        "def _cached_helper():\n"
        "    return 3\n"
    )
    assert_no_errors(
        UnusedPrivateHelper, clean, options={"ignore_decorators": ["lru_cache"]}
    )
    assert_error_count(UnusedPrivateHelper, clean, 1)


def test_cc107_handles_forward_references_and_local_shadowing() -> None:
    source = (
        "def caller():\n"
        "    return _stepdown_helper()\n"
        "def _stepdown_helper():\n"
        "    return 1\n"
        "def _shadowed_dead():\n"
        "    return 2\n"
        "def shadows():\n"
        "    _shadowed_dead = 3\n"
        "    return _shadowed_dead\n"
    )
    diags = assert_error_count(UnusedPrivateHelper, source, 1)
    assert "_shadowed_dead" in diags[0].message
    assert "_stepdown_helper" not in diags[0].message


def test_cc207_excessive_direct_bases_and_exemptions() -> None:
    clean = (
        "from typing import Generic, Protocol, TypeVar\n"
        'T = TypeVar("T")\n'
        "class Good(A, B, C, Generic[T], Protocol, metaclass=Meta):\n"
        "    pass\n"
    )
    assert_no_errors(TooManyBaseClasses, clean)

    violating = (
        "class Bad(A, B, C, D, Generic[T]):\n    pass\n"
        "class AlsoBad(A, B, typing.Protocol, C, D):\n    pass\n"
    )
    diags = assert_error_count(TooManyBaseClasses, violating, 2)
    assert all(d.code == "CC207" and d.severity == Severity.WARNING for d in diags)
    assert "4 > 3" in diags[0].message
    assert "composition" in diags[0].message.lower()


def test_cc207_configurable_limits_and_ignored_bases() -> None:
    assert_error_count(
        TooManyBaseClasses,
        "class Two(A, B):\n    pass\n",
        1,
        options={"max_bases": 1},
    )
    assert_error_count(
        TooManyBaseClasses,
        "class WithGeneric(A, B, C, Generic[T]):\n    pass\n",
        1,
        options={"ignore_bases": []},
    )


def test_cc306_nested_ternary_and_nested_scope_isolation() -> None:
    clean = (
        "simple = 1 if flag else 2\n"
        "with_lambda = (lambda v: 1 if v else 2)(x) if flag else 3\n"
        "def outer(flag):\n"
        "    def inner(v):\n"
        "        return 1 if v else 2\n"
        "    return inner(1) if flag else 0\n"
    )
    assert_no_errors(NestedTernary, clean)

    violating = (
        "a = 1 if x else (2 if y else 3)\n"
        "b = (1 if p else 2) if q else 3\n"
        "deep = 1 if x else (2 if y else (3 if z else 4))\n"
    )
    diags = assert_error_count(NestedTernary, violating, 3)
    assert all(d.code == "CC306" and d.severity == Severity.WARNING for d in diags)
    assert "2 > 1" in diags[0].message
    assert "3 > 1" in diags[2].message


def test_cc308_global_statement_and_test_exclusion() -> None:
    clean = "def f():\n    x = 1\n    return x\n"
    assert_no_errors(GlobalStatement, clean)

    violating = "STATE = 0\ndef mutate():\n    global STATE\n    STATE += 1\n"
    diags = assert_error_count(GlobalStatement, violating, 1, filename="app/mod.py")
    assert diags[0].code == "CC308"
    assert diags[0].severity == Severity.WARNING
    assert "STATE" in diags[0].message

    assert_no_errors(GlobalStatement, violating, filename="tests/test_mod.py")
    assert_error_count(
        GlobalStatement,
        violating,
        1,
        options={"exclude_tests": False},
        filename="tests/test_mod.py",
    )


def test_cc309_broad_exception_swallowing_and_exemptions() -> None:
    assert_no_errors(BroadExceptionSwallowed, CC309_CLEAN_SAMPLE, filename="app/mod.py")
    diags = assert_error_count(
        BroadExceptionSwallowed, CC309_VIOLATING_SAMPLE, 5, filename="app/mod.py"
    )
    assert all(d.code == "CC309" and d.severity == Severity.WARNING for d in diags)
    assert_no_errors(
        BroadExceptionSwallowed, CC309_VIOLATING_SAMPLE, filename="tests/test_bad.py"
    )


def test_cc310_missing_exception_chaining_and_bare_raise_exemption() -> None:
    assert_no_errors(MissingExceptionChaining, CC310_CLEAN_SAMPLE)
    violating = (
        "def broken(raw):\n"
        "    try:\n"
        "        return int(raw)\n"
        "    except ValueError:\n"
        "        raise RuntimeError('unchained')\n"
    )
    diags = assert_error_count(MissingExceptionChaining, violating, 1)
    assert diags[0].code == "CC310"
    assert diags[0].severity == Severity.WARNING
    assert "from" in diags[0].message


def test_cc311_oversized_try_block_excludes_clauses_and_nested_defs() -> None:
    try_body = "\n".join(f"        x_{i} = {i}" for i in range(20))
    except_body = "\n".join(f"        e_{i} = {i}" for i in range(30))
    nested_def = "\n".join(
        ["        def inner():"] + [f"            y_{i} = {i}" for i in range(10)]
    )
    clean = (
        "def ok():\n"
        f"    try:\n{try_body}\n    except ValueError:\n{except_body}\n"
        f"    try:\n        a = 1\n{nested_def}\n        b = 2\n"
        "    except RuntimeError:\n        raise\n"
    )
    assert_no_errors(OversizedTryBlock, clean)


def test_cc311_flags_oversized_try_suite_and_supports_custom_limit() -> None:
    too_long = (
        "def bad():\n    try:\n"
        + "\n".join(f"        x_{i} = {i}" for i in range(21))
        + "\n    except ValueError:\n        raise\n"
    )
    diags = assert_error_count(OversizedTryBlock, too_long, 1)
    assert diags[0].code == "CC311"
    assert diags[0].severity == Severity.WARNING
    assert "21 > 20" in diags[0].message
    assert_error_count(
        OversizedTryBlock,
        "def s():\n    try:\n        a = 1\n        b = 2\n    except Exception:\n        raise\n",
        1,
        options={"max_lines": 1},
    )


@pytest.mark.parametrize(
    ("rule_cls", "option", "bad_value"),
    [
        (UnusedPrivateHelper, "ignore_decorators", "pytest.fixture"),
        (TooManyBaseClasses, "max_bases", -1),
        (TooManyBaseClasses, "ignore_bases", "Generic"),
        (GlobalStatement, "exclude_tests", "yes"),
        (BroadExceptionSwallowed, "exclude_tests", 1),
        (OversizedTryBlock, "max_lines", True),
    ],
)
def test_rcc10_invalid_options_raise_value_error(
    rule_cls: type, option: str, bad_value: object
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError, match=option):
        rule.configure({option: bad_value})

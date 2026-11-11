"""Tests for RCC-6 maturing heuristic rules (CC105, CC204-206, CC304-305, CC503-504, CC602-603)."""

from __future__ import annotations

import pytest
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors

from rude_clean_code.rules.class_heuristics import (
    ExcessiveConstructorDependencies,
    MultipleResponsibilities,
    OversizedInterfaceSurface,
)
from rude_clean_code.rules.complexity_heuristics import (
    ComplexExpression,
    UnnecessaryAbstraction,
)
from rude_clean_code.rules.dry_heuristics import (
    RepeatedConstantDefinition,
    RepeatedValidation,
)
from rude_clean_code.rules.function_heuristics import BooleanFlagParameter
from rude_clean_code.rules.solid_heuristics import (
    InterfaceSegregationIndicator,
    SuspiciousOverriddenMethod,
)


def test_cc105_boolean_flag_parameter_detects_mode_flags_and_allows_extension() -> None:
    clean = (
        "def save_order(order, validate: Callable[[object], bool]) -> None:\n"
        "    validate(order)\n\n"
        "def toggle(enabled: bool = True) -> bool:\n"
        "    return not enabled\n"
    )
    assert_no_errors(BooleanFlagParameter, clean)

    violating = (
        "def export_data(records, dry_run: bool = False, validate=True) -> None:\n"
        "    pass\n"
    )
    diags = assert_error_count(BooleanFlagParameter, violating, 2)
    assert all(d.code == "CC105" and d.severity == Severity.INFO for d in diags)
    assert "dry_run" in diags[0].message
    assert "suggest" in diags[0].message.lower()

    custom = "def deploy(target, canary: bool = False) -> None:\n    pass\n"
    assert_no_errors(BooleanFlagParameter, custom)
    assert_error_count(
        BooleanFlagParameter, custom, 1, options={"flag_names": ["canary"]}
    )


def test_cc204_constructor_dependencies_clean_and_untyped() -> None:
    clean = (
        "class OrderService:\n"
        "    def __init__(self, repo: Repo, mailer: Mailer, *, debug: bool = False) -> None:\n"
        "        self.repo = repo\n"
        "        self.mailer = mailer\n"
        "        self.debug = debug\n\n"
        "class UntypedBag:\n"
        "    def __init__(self, a, b, c, d, e, f, g):\n"
        "        pass\n"
    )
    assert_no_errors(ExcessiveConstructorDependencies, clean)


def test_cc204_constructor_dependencies_exceeding_limit() -> None:
    violating = (
        "class MegaCoordinator:\n"
        "    def __init__(self, a: A, b: B, c: C, d: D, e: E, f: F) -> None:\n"
        "        pass\n"
    )
    diags = assert_error_count(ExcessiveConstructorDependencies, violating, 1)
    assert diags[0].code == "CC204"
    assert diags[0].severity == Severity.INFO
    assert "6 > 5" in diags[0].message
    assert_no_errors(
        ExcessiveConstructorDependencies, violating, options={"max_dependencies": 6}
    )


def test_cc205_cohesive_class_stays_clean() -> None:
    cohesive = (
        "class OrderAccumulator:\n"
        "    def __init__(self) -> None:\n"
        "        self.items = []\n"
        "        self.total = 0\n\n"
        "    def add(self, price: int) -> None:\n"
        "        self.items.append(price)\n"
        "        self.total += price\n\n"
        "    def reset(self) -> None:\n"
        "        self.items.clear()\n"
        "        self.total = 0\n\n"
        "    def summary(self) -> int: return self.total\n"
        "    def count(self) -> int: return len(self.items)\n"
        "    def average(self) -> float: return self.summary() / self.count()\n"
    )
    assert_no_errors(MultipleResponsibilities, cohesive)


def test_cc205_multiple_responsibilities_disjoint_clusters() -> None:
    disjoint = (
        "class GodWorker:\n"
        "    def save(self) -> None: self.db.write()\n"
        "    def load(self) -> None: self.db.read()\n"
        "    def send_email(self) -> None: self.mailer.send()\n"
        "    def bounce(self) -> None: self.mailer.bounce()\n"
        "    def rate(self) -> None: self.tax.compute()\n"
        "    def audit_tax(self) -> None: self.tax.audit()\n"
    )
    diags = assert_error_count(MultipleResponsibilities, disjoint, 1)
    assert diags[0].code == "CC205"
    assert diags[0].severity == Severity.INFO
    assert "3 > 2" in diags[0].message
    assert "violat" not in diags[0].message.lower()


def test_cc206_oversized_interface_surface() -> None:
    clean_lines = ["class FocusedClient:\n", "    def _private(self): pass\n"]
    clean_lines.extend(f"    def op_{idx}(self): pass\n" for idx in range(10))
    assert_no_errors(OversizedInterfaceSurface, "".join(clean_lines))

    wide_lines = ["class WideClient:\n"]
    wide_lines.extend(f"    def op_{idx}(self): pass\n" for idx in range(11))
    diags = assert_error_count(OversizedInterfaceSurface, "".join(wide_lines), 1)
    assert diags[0].code == "CC206"
    assert diags[0].severity == Severity.INFO
    assert "11 > 10" in diags[0].message
    assert "per-file" in diags[0].message.lower()


def test_cc304_unnecessarily_complex_expression() -> None:
    clean = (
        "MAPPING = {'a': fn(1), 'b': fn(2), 'c': fn(3), 'd': fn(4), 'e': fn(5), 'f': fn(6)}\n"
        "def simple(x, y):\n"
        "    return (x + 1) * (y - 2)\n"
    )
    assert_no_errors(ComplexExpression, clean)

    dense = (
        "def eval_dense(items, a, b, c, d):\n"
        "    return sum(x.val() + a * b - c // d for x in items if x.ok() and (x.flag or d > 0))\n"
    )
    diags = assert_error_count(ComplexExpression, dense, 1)
    assert diags[0].code == "CC304"
    assert diags[0].severity == Severity.INFO


def test_cc305_silent_for_pure_interfaces_and_absent_base() -> None:
    pure_interface_module = (
        "from typing import Protocol\n\n"
        "class OrderRepository(Protocol):\n"
        "    def save(self, order_id: str) -> None: ...\n"
    )
    assert_no_errors(UnnecessaryAbstraction, pure_interface_module)

    absent_base_name = (
        "class BaseSender:\n    pass\n\n"
        "class EmailSender(BaseSender):\n    def send(self) -> None: pass\n"
    )
    assert_no_errors(UnnecessaryAbstraction, absent_base_name)

    with_consumer = (
        "from abc import ABC, abstractmethod\n\n"
        "class Storage(ABC):\n"
        "    @abstractmethod\n    def read(self) -> str: ...\n\n"
        "class MemoryStorage(Storage):\n"
        "    def read(self) -> str: return ''\n\n"
        "def load_all(store: Storage) -> str:\n    return store.read()\n"
    )
    assert_no_errors(UnnecessaryAbstraction, with_consumer)


def test_cc305_flags_single_impl_without_in_file_consumer() -> None:
    speculative = (
        "from abc import ABC, abstractmethod\n\n"
        "class Notifier(ABC):\n"
        "    @abstractmethod\n    def notify(self, msg: str) -> None: ...\n\n"
        "class EmailNotifier(Notifier):\n"
        "    def notify(self, msg: str) -> None: print(msg)\n"
    )
    diags = assert_error_count(UnnecessaryAbstraction, speculative, 1)
    assert diags[0].code == "CC305"
    assert diags[0].severity == Severity.INFO
    assert "1" in diags[0].message


def test_cc503_repeated_validation_logic_clean_vs_repeated() -> None:
    clean = (
        "def a(user):\n    if user is None:\n        return None\n    return user.id\n\n"
        "def b(account):\n    if account is None:\n        return None\n    return account.id\n\n"
        "def c(order):\n    if order is None:\n        return None\n    return order.id\n"
    )
    assert_no_errors(RepeatedValidation, clean)

    repeated = (
        "def f1(name):\n    if not isinstance(name, str): raise TypeError('s')\n"
        "    if not name: raise ValueError('e')\n    return name\n\n"
        "def f2(label):\n    if not isinstance(label, str): raise TypeError('s')\n"
        "    if not label: raise ValueError('e')\n    return label\n\n"
        "def f3(alias):\n    if not isinstance(alias, str): raise TypeError('s')\n"
        "    if not alias: raise ValueError('e')\n    return alias\n"
    )
    diags = assert_error_count(RepeatedValidation, repeated, 1)
    assert diags[0].code == "CC503"
    assert diags[0].severity == Severity.INFO
    assert "3 >= 3" in diags[0].message


def test_cc504_repeated_constant_definitions_file_scope_subset() -> None:
    clean = (
        "DEFAULT_ZERO = 0\nRETRY_ONE = 1\nFALLBACK_EMPTY = ''\n"
        "ENABLED_A = False\nENABLED_B = False\nENABLED_C = False\n"
        "MAX_RETRIES = 30\nMAX_WAIT = 30\n"
    )
    assert_no_errors(RepeatedConstantDefinition, clean)

    violating = "API_TIMEOUT = 30\nCACHE_TTL = 30\nPOOL_SECONDS = 30\n"
    diags = assert_error_count(RepeatedConstantDefinition, violating, 1)
    assert diags[0].code == "CC504"
    assert "file" in diags[0].message.lower()
    assert "3 >= 3" in diags[0].message


def test_cc602_suspicious_override_clean_and_absent_base() -> None:
    external = (
        "class CustomHandler(ExternalHandler):\n"
        "    def handle(self, req):\n        raise NotImplementedError\n"
    )
    assert_no_errors(SuspiciousOverriddenMethod, external)

    clean = (
        "from abc import ABC, abstractmethod\n\n"
        "class Base:\n"
        "    def __init__(self, x: int = 1) -> None: self.x = x\n"
        "    def render(self, mode: str = 'fast') -> str: return mode\n\n"
        "class Child(Base):\n"
        "    def __init__(self, x: int) -> None: self.x = x\n"
        "    def render(self, mode: str = 'slow') -> str: return mode\n\n"
        "class AbstractRepo(ABC):\n"
        "    @abstractmethod\n    def save(self) -> str: ...\n\n"
        "class ReadOnlyRepo(AbstractRepo):\n"
        "    def save(self) -> str: raise NotImplementedError\n\n"
        "class TypedStub(Base):\n"
        "    def render(self, mode: str = 'fast') -> str: ...\n"
    )
    assert_no_errors(SuspiciousOverriddenMethod, clean)


def test_cc602_suspicious_override_detects_lsp_smells() -> None:
    violating = (
        "class BaseService:\n"
        "    def run(self, mode: str = 'fast') -> str: return mode\n"
        "    def ping(self) -> str: return 'ok'\n"
        "    def reset(self) -> None: return None\n\n"
        "class BrokenService(BaseService):\n"
        "    def run(self, mode: str) -> str: return mode\n"
        "    def ping(self) -> str: return None\n"
        "    def reset(self) -> None: raise NotImplementedError\n"
    )
    diags = assert_error_count(SuspiciousOverriddenMethod, violating, 3)
    assert all(d.code == "CC602" and d.severity == Severity.INFO for d in diags)
    assert all("violat" not in d.message.lower() for d in diags)


def test_cc603_interface_segregation_silent_without_visible_base() -> None:
    external_base = (
        "class BrokenMock(ExternalFatInterface):\n"
        "    def a(self): raise NotImplementedError\n"
        "    def b(self): raise NotImplementedError\n"
        "    def c(self): raise NotImplementedError\n"
    )
    assert_no_errors(InterfaceSegregationIndicator, external_base)

    violating = (
        "from abc import ABC\n\n"
        "class FatRepo(ABC):\n"
        "    def create(self): ...\n    def update(self): ...\n"
        "    def delete(self): ...\n    def list_all(self): ...\n\n"
        "class ReadOnlyRepo(FatRepo):\n"
        "    def create(self): raise NotImplementedError\n"
        "    def update(self): raise NotImplementedError\n"
        "    def delete(self): raise NotImplementedError\n"
        "    def list_all(self): return []\n"
    )
    diags = assert_error_count(InterfaceSegregationIndicator, violating, 1)
    assert diags[0].code == "CC603"
    assert diags[0].severity == Severity.INFO
    assert "3 > 2" in diags[0].message


@pytest.mark.parametrize(
    ("rule_cls", "option", "bad_value"),
    [
        (BooleanFlagParameter, "flag_names", "dry_run"),
        (MultipleResponsibilities, "max_clusters", 0),
        (MultipleResponsibilities, "min_methods", False),
        (RepeatedValidation, "min_functions", 1),
        (RepeatedConstantDefinition, "min_occurrences", 1),
        (InterfaceSegregationIndicator, "max_unimplemented", -1),
    ],
)
def test_rcc6_invalid_options_raise_value_error(
    rule_cls: type, option: str, bad_value: object
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError, match=option):
        rule.configure({option: bad_value})

"""Tests for config-driven design-pattern boundary rules (CC801-CC805)."""

from __future__ import annotations

from pathlib import Path

import pytest
from rude.core import CheckOptions, Linter
from rude.core.types import Severity
from rude.testing import assert_error_count, assert_no_errors, assert_no_fix

from rude_clean_code.rules.patterns import (
    ConcreteServiceConstruction,
    DataAccessOutsideRepository,
    HandlerMissingDecorator,
    ProductInstantiatedOutsideFactory,
    StrategyProtocolViolation,
)

FIXTURE_APP = Path(__file__).resolve().parent / "fixtures" / "consumer_app"


def _run_rule_on_fixture(rule: object) -> list[tuple[Path, object]]:
    linter = Linter()
    linter.register(rule)  # type: ignore[arg-type]
    return list(linter.check_paths_parallel([FIXTURE_APP]))


@pytest.mark.parametrize(
    "rule_cls",
    [
        DataAccessOutsideRepository,
        ProductInstantiatedOutsideFactory,
        StrategyProtocolViolation,
        HandlerMissingDecorator,
        ConcreteServiceConstruction,
    ],
)
def test_cc80x_rules_are_inert_when_unconfigured(rule_cls: type) -> None:
    rule = rule_cls()
    assert _run_rule_on_fixture(rule) == []
    assert "precondition" in (rule_cls.__doc__ or "").lower()


def test_cc801_flags_data_access_outside_repositories_and_spares_repository() -> None:
    partial = DataAccessOutsideRepository()
    partial.configure({"data_modules": ["sqlalchemy"]})
    assert _run_rule_on_fixture(partial) == []

    rule = DataAccessOutsideRepository()
    rule.configure(
        {
            "data_modules": ["sqlalchemy"],
            "repository_paths": ["repositories/"],
        }
    )
    results = _run_rule_on_fixture(rule)
    flagged = {path.relative_to(FIXTURE_APP).as_posix() for path, _ in results}
    assert flagged == {"domain/order.py", "services/checkout_service.py"}
    assert "repositories/sql_order_repo.py" not in flagged
    assert all(
        d.code == "CC801" and d.severity == Severity.WARNING  # type: ignore[attr-defined]
        for _, d in results
    )


def test_cc802_flags_product_construction_outside_factories_and_create_funcs() -> None:
    rule = ProductInstantiatedOutsideFactory()
    rule.configure(
        {
            "product_classes": ["StripeGateway"],
            "factory_paths": ["factories/"],
            "exclude_paths": ["composition.py"],
        }
    )
    results = _run_rule_on_fixture(rule)
    assert len(results) == 1
    path, diag = results[0]
    assert path.relative_to(FIXTURE_APP).as_posix() == "services/checkout_service.py"
    assert diag.code == "CC802"  # type: ignore[attr-defined]
    assert diag.severity == Severity.WARNING  # type: ignore[attr-defined]
    assert diag.location.line == 23  # type: ignore[attr-defined]


def test_cc803_checks_strategy_inheritance_and_method_on_fixture() -> None:
    rule = StrategyProtocolViolation()
    rule.configure(
        {
            "strategy_base": "PaymentStrategy",
            "required_method": "pay",
            "strategy_paths": ["strategies/"],
        }
    )
    results = _run_rule_on_fixture(rule)
    assert len(results) == 2
    for path, diag in results:
        assert path.relative_to(FIXTURE_APP).as_posix() == "strategies/broken.py"
        assert diag.code == "CC803"  # type: ignore[attr-defined]
        assert diag.severity == Severity.WARNING  # type: ignore[attr-defined]
    messages = "\n".join(d.message for _, d in results)  # type: ignore[attr-defined]
    assert "UnboundStrategy" in messages
    assert "IncompleteStrategy" in messages


def test_cc803_handles_generic_decorated_and_metaclass_strategies() -> None:
    options = {
        "strategy_base": ["PaymentStrategy"],
        "required_method": "pay",
        "strategy_paths": ["strategies/"],
        "exclude_paths": ["strategies/ignored.py"],
    }
    clean = (
        "from typing import Generic, TypeVar\nT = TypeVar('T')\n"
        "class GenericCard(pkg.PaymentStrategy[T]):\n"
        "    @override\n"
        "    async def pay(self, amount: int) -> bool:\n"
        "        def _inner():\n"
        "            class LocalMeta:\n                pass\n"
        "            return LocalMeta\n"
        "        return True\n"
    )
    assert_no_errors(
        StrategyProtocolViolation,
        clean,
        options=options,
        filename="strategies/generic.py",
    )
    assert_error_count(
        StrategyProtocolViolation,
        "class MetaStrat(metaclass=Meta):\n    pass\n",
        1,
        options=options,
        filename="strategies/meta.py",
    )


def test_cc804_flags_missing_handler_decorator_and_spares_helpers() -> None:
    rule = HandlerMissingDecorator()
    rule.configure(
        {
            "required_decorator": "register_handler",
            "handler_paths": ["handlers/"],
            "exclude_paths": ["handlers/ignored.py"],
        }
    )
    results = _run_rule_on_fixture(rule)
    assert len(results) == 1
    path, diag = results[0]
    assert path.relative_to(FIXTURE_APP).as_posix() == "handlers/orders.py"
    assert diag.code == "CC804"  # type: ignore[attr-defined]
    assert diag.severity == Severity.WARNING  # type: ignore[attr-defined]
    assert "handle_cancel_order" in diag.message  # type: ignore[attr-defined]


def test_cc804_glob_decorators_methods_and_ignore_private_option() -> None:
    assert_error_count(
        HandlerMissingDecorator,
        "def _private_handler():\n    pass\n",
        1,
        options={
            "required_decorator": ["router.*"],
            "handler_paths": ["handlers/"],
            "ignore_private": False,
        },
        filename="handlers/routes.py",
    )
    assert_no_errors(
        HandlerMissingDecorator,
        "class Helper:\n    def method(self):\n        pass\n"
        "@router.post('/orders')\nasync def create_order():\n    pass\n",
        options={"required_decorator": ["router.*"], "handler_paths": ["handlers/"]},
        filename="handlers/routes.py",
    )


def test_cc805_emits_info_for_direct_service_construction_outside_composition() -> None:
    rule = ConcreteServiceConstruction()
    rule.configure(
        {
            "service_classes": ["EmailNotifier"],
            "only_paths": ["services/", "composition.py"],
            "exclude_paths": ["composition.py"],
        }
    )
    results = _run_rule_on_fixture(rule)
    assert len(results) == 1
    path, diag = results[0]
    assert path.relative_to(FIXTURE_APP).as_posix() == "services/checkout_service.py"
    assert diag.code == "CC805"  # type: ignore[attr-defined]
    assert diag.severity == Severity.INFO  # type: ignore[attr-defined]
    msg = diag.message.lower()  # type: ignore[attr-defined]
    assert "suggests" in msg and "consider" in msg


def test_cc805_allows_self_constructors_and_emits_no_fix() -> None:
    self_ctor = (
        "class EmailNotifier:\n"
        "    @classmethod\n    def from_env(cls):\n        return EmailNotifier()\n"
        "    def helper(self):\n        return super().EmailNotifier()\n"
    )
    assert_no_errors(
        ConcreteServiceConstruction,
        self_ctor,
        options={"service_classes": ["EmailNotifier"]},
        filename="services/notifier.py",
    )
    assert_no_fix(
        ConcreteServiceConstruction,
        "def run():\n    return EmailNotifier()\n",
        options={"service_classes": ["EmailNotifier"]},
        filename="services/runner.py",
    )


def test_cc80x_multiprocess_execution_preserves_pattern_configs() -> None:
    rules = []
    r801 = DataAccessOutsideRepository()
    r801.configure(
        {
            "data_modules": ["sqlalchemy"],
            "repository_paths": ["repositories/"],
            "exclude_paths": ["migrations/"],
        }
    )
    r803 = StrategyProtocolViolation()
    r803.configure(
        {
            "strategy_base": "PaymentStrategy",
            "required_method": "pay",
            "strategy_paths": ["strategies/"],
        }
    )
    rules.extend([r801, r803])
    linter = Linter()
    linter.register_all(rules)
    results = list(linter.check_paths_parallel([FIXTURE_APP], CheckOptions(workers=2)))
    codes = {diag.code for _, diag in results}
    assert codes == {"CC801", "CC803"}


@pytest.mark.parametrize(
    ("rule_cls", "options"),
    [
        (DataAccessOutsideRepository, {"data_modules": "sqlalchemy"}),
        (ProductInstantiatedOutsideFactory, {"product_classes": [1]}),
        (StrategyProtocolViolation, {"strategy_base": 42}),
        (StrategyProtocolViolation, {"strategy_base": ""}),
        (StrategyProtocolViolation, {"strategy_base": [" "]}),
        (StrategyProtocolViolation, {"required_method": True}),
        (HandlerMissingDecorator, {"required_decorator": 99}),
        (HandlerMissingDecorator, {"ignore_private": "yes"}),
        (ConcreteServiceConstruction, {"service_classes": "EmailNotifier"}),
    ],
)
def test_cc80x_invalid_options_raise_value_error(
    rule_cls: type, options: dict[str, object]
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError):
        rule.configure(options)

"""Config-driven design-pattern boundary rules (CC801-CC805)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    base_candidate_names,
    definition_name,
    is_module_level_definition,
    node_decorators,
    parse_bool_option,
)
from rude_clean_code.rules._architecture import (
    LayerDependencySpec,
    any_spec_matches_file,
    check_import_against_specs,
    parse_optional_str_or_list_option,
)
from rude_clean_code.rules._symbol_matching import (
    ScopedCallRule,
    apply_str_list_options,
    call_target_candidates,
    direct_method_names,
    enclosing_class_name,
    enclosing_function_names,
    file_matches_scope,
    match_configured_symbol,
    matches_decorator,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext


def _format_data_access_message(
    module_name: str,
    matched_prefix: str,
    spec: LayerDependencySpec,
) -> str:
    del spec
    return (
        f"Data access import '{module_name}' (matches '{matched_prefix}') outside "
        "configured repository paths; encapsulate persistence inside a repository"
    )


def _short_symbol_names(symbols: tuple[str, ...]) -> frozenset[str]:
    return frozenset(item.rsplit(".", maxsplit=1)[-1] for item in symbols)


def _class_inherits_any(class_node: Node, expected_bases: tuple[str, ...]) -> bool:
    for base in class_node.bases:
        if base.type == "keyword_argument":
            continue
        candidates = base_candidate_names(base)
        if candidates and match_configured_symbol(
            candidates[0], candidates[-1], expected_bases
        ):
            return True
    return False


class DataAccessOutsideRepository(Rule):
    """CC801: Database or ORM modules imported outside configured repository paths.

    Precondition: configure only if your project adopts the Repository pattern;
    otherwise leave this rule unconfigured so it stays inert.
    """

    code: ClassVar[str] = "CC801"
    message: ClassVar[str] = "Data access module imported outside repository layer"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {
        NodeType.IMPORT_STATEMENT,
        NodeType.IMPORT_FROM_STATEMENT,
    }

    data_modules: tuple[str, ...] = ()
    repository_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.data_modules = ()
        self.repository_paths = ()
        self.exclude_paths = ()

    def _as_specs(self) -> tuple[LayerDependencySpec, ...]:
        if not self.data_modules or not self.repository_paths:
            return ()
        return (
            LayerDependencySpec(
                only_paths=(),
                exclude_paths=self.repository_paths + self.exclude_paths,
                forbidden_modules=self.data_modules,
            ),
        )

    def should_check_file(self, context: FileContext) -> bool:
        """Stay inert unless both ``data_modules`` and ``repository_paths`` apply."""
        return any_spec_matches_file(context, self._as_specs())

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``data_modules``, ``repository_paths``, and ``exclude_paths``."""
        apply_str_list_options(
            self, options, "data_modules", "repository_paths", "exclude_paths"
        )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag imports matching ``data_modules`` outside ``repository_paths``."""
        yield from check_import_against_specs(
            self, node, self._as_specs(), _format_data_access_message
        )


class ProductInstantiatedOutsideFactory(ScopedCallRule):
    """CC802: Product class constructed outside configured factories or ``create_*``.

    Precondition: configure only if your project adopts Factory encapsulation
    for product construction; otherwise leave this rule unconfigured.
    """

    code: ClassVar[str] = "CC802"
    message: ClassVar[str] = "Product class instantiated outside factory"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CALL}
    target_option_name: ClassVar[str] = "product_classes"

    product_classes: tuple[str, ...] = ()
    factory_paths: tuple[str, ...] = ()

    def __init__(self) -> None:
        super().__init__()
        self.factory_paths = ()

    def should_check_file(self, context: FileContext) -> bool:
        """Skip factory paths and exclusions; stay inert if ``product_classes`` empty."""
        if not self.product_classes:
            return False
        return file_matches_scope(
            context,
            only_paths=self.only_paths,
            exclude_paths=self.factory_paths + self.exclude_paths,
        )

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``product_classes``, ``factory_paths``, and path filters."""
        self._configure_scoped_call(options)
        apply_str_list_options(self, options, "factory_paths")

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag product instantiations outside ``factory_paths`` and ``create_*``."""
        matched = self._matched_call_target(node)
        if matched is None:
            return
        if any(fn.startswith("create_") for fn in enclosing_function_names(node)):
            return
        yield self.diagnostic(
            node,
            f"Product class '{matched}' instantiated outside configured factories "
            "or a 'create_*' factory function; delegate creation to a factory",
        )


class StrategyProtocolViolation(Rule):
    """CC803: Strategy class missing configured strategy base or required method.

    Precondition: configure only if your project organizes concrete strategies
    under dedicated paths implementing a Strategy base or protocol.
    """

    code: ClassVar[str] = "CC803"
    message: ClassVar[str] = "Strategy class violates configured strategy protocol"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CLASS_DEFINITION}

    strategy_bases: tuple[str, ...] = ()
    required_methods: tuple[str, ...] = ()
    strategy_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.strategy_bases = ()
        self.required_methods = ()
        self.strategy_paths = ()
        self.exclude_paths = ()

    def should_check_file(self, context: FileContext) -> bool:
        """Apply only under ``strategy_paths`` once base or method is configured."""
        if not self.strategy_paths or (
            not self.strategy_bases and not self.required_methods
        ):
            return False
        return file_matches_scope(
            context, only_paths=self.strategy_paths, exclude_paths=self.exclude_paths
        )

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``strategy_base``, ``required_method``, and path filters."""
        if "strategy_base" in options:
            self.strategy_bases = parse_optional_str_or_list_option(
                self.code, "strategy_base", options["strategy_base"]
            )
        if "required_method" in options:
            self.required_methods = parse_optional_str_or_list_option(
                self.code, "required_method", options["required_method"]
            )
        apply_str_list_options(self, options, "strategy_paths", "exclude_paths")

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag top-level strategy classes missing expected base or method."""
        if not is_module_level_definition(node):
            return
        name = definition_name(node)
        if name in _short_symbol_names(self.strategy_bases):
            return
        missing: list[str] = []
        if self.strategy_bases and not _class_inherits_any(node, self.strategy_bases):
            missing.append(f"inherit '{'/'.join(self.strategy_bases)}'")
        if self.required_methods:
            defined = direct_method_names(node)
            absent = [m for m in self.required_methods if m not in defined]
            if absent:
                missing.append(f"define method '{', '.join(absent)}'")
        if missing:
            yield self.diagnostic(
                node, f"Strategy class '{name}' must {' and '.join(missing)}"
            )


class HandlerMissingDecorator(Rule):
    """CC804: Public top-level handler missing its registration decorator.

    Precondition: configure only if your project uses decorator-registered
    handlers (such as CLI commands, routes, or message handlers).
    """

    code: ClassVar[str] = "CC804"
    message: ClassVar[str] = "Handler function is missing required decorator"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}

    required_decorators: tuple[str, ...] = ()
    handler_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    ignore_private: bool = True

    def __init__(self) -> None:
        self.required_decorators = ()
        self.handler_paths = ()
        self.exclude_paths = ()
        self.ignore_private = True

    def should_check_file(self, context: FileContext) -> bool:
        """Apply only under ``handler_paths`` once ``required_decorator`` is set."""
        if not self.handler_paths or not self.required_decorators:
            return False
        return file_matches_scope(
            context, only_paths=self.handler_paths, exclude_paths=self.exclude_paths
        )

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``required_decorator``, ``handler_paths``, and ``ignore_private``."""
        if "required_decorator" in options:
            self.required_decorators = parse_optional_str_or_list_option(
                self.code, "required_decorator", options["required_decorator"]
            )
        apply_str_list_options(self, options, "handler_paths", "exclude_paths")
        if "ignore_private" in options:
            self.ignore_private = parse_bool_option(
                self.code, "ignore_private", options["ignore_private"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag top-level handlers lacking a configured registration decorator."""
        if not is_module_level_definition(node):
            return
        name = definition_name(node)
        if self.ignore_private and name.startswith("_"):
            return
        if matches_decorator(node_decorators(node), self.required_decorators):
            return
        expected = ", ".join(f"@{dec}" for dec in self.required_decorators)
        yield self.diagnostic(
            node,
            f"Handler '{name}' is missing required registration decorator ({expected})",
        )


class ConcreteServiceConstruction(ScopedCallRule):
    """CC805: Service class constructed directly instead of via dependency injection.

    Precondition: configure only if your project wires collaborators via
    constructor dependency injection and isolates construction in composition
    roots.
    """

    code: ClassVar[str] = "CC805"
    message: ClassVar[str] = "Direct service construction suggests bypassed DI"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CALL}
    target_option_name: ClassVar[str] = "service_classes"

    service_classes: tuple[str, ...] = ()

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``service_classes``, ``only_paths``, and ``exclude_paths``."""
        self._configure_scoped_call(options)

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag non-self construction of configured service classes outside exclusions."""
        candidates = call_target_candidates(node)
        if candidates is None:
            return
        matched = match_configured_symbol(
            candidates[0], candidates[1], self.service_classes
        )
        if matched is None or enclosing_class_name(node) == candidates[1]:
            return
        yield self.diagnostic(
            node,
            f"Constructing service '{matched}' directly here suggests bypassed "
            "dependency injection; consider accepting it as a constructor parameter "
            "and wiring it at a composition root",
        )


PATTERN_RULES: list[type[Rule]] = [
    DataAccessOutsideRepository,
    ProductInstantiatedOutsideFactory,
    StrategyProtocolViolation,
    HandlerMissingDecorator,
    ConcreteServiceConstruction,
]

__all__ = [
    "PATTERN_RULES",
    "ConcreteServiceConstruction",
    "DataAccessOutsideRepository",
    "HandlerMissingDecorator",
    "ProductInstantiatedOutsideFactory",
    "StrategyProtocolViolation",
]

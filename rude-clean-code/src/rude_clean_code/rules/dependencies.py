"""Config-driven architectural dependency and boundary rules (CC701, CC702, CC704)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code.rules._architecture import (
    LayerDependencySpec,
    any_spec_matches_file,
    check_import_against_specs,
    parse_layer_specs,
)
from rude_clean_code.rules._symbol_matching import (
    ScopedCallRule,
    apply_str_list_options,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext


def _format_layer_dependency_message(
    module_name: str,
    matched_prefix: str,
    spec: LayerDependencySpec,
) -> str:
    layer_desc = (
        f"paths matching {', '.join(spec.only_paths)}"
        if spec.only_paths
        else "this file"
    )
    return (
        f"Forbidden import '{module_name}' (matches '{matched_prefix}') in {layer_desc}; "
        "depend on a domain abstraction or port instead"
    )


class ForbiddenLayerDependency(Rule):
    """CC704: Forbidden dependency from a configured layer to a module prefix.

    Generalizes ``CC701`` with consumer-declared ``(from-layer, forbidden-module)``
    rules. Inert until ``forbidden`` entries are configured.
    """

    code: ClassVar[str] = "CC704"
    message: ClassVar[str] = "Forbidden architectural layer dependency"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {
        NodeType.IMPORT_STATEMENT,
        NodeType.IMPORT_FROM_STATEMENT,
    }

    forbidden: tuple[LayerDependencySpec, ...] = ()

    def __init__(self) -> None:
        self.forbidden = ()

    def should_check_file(self, context: FileContext) -> bool:
        """Stay inert unless a configured dependency rule applies to *context*."""
        return any_spec_matches_file(context, self.forbidden)

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``forbidden`` layer-to-module dependency rules."""
        if "forbidden" in options:
            self.forbidden = parse_layer_specs(
                self.code, "forbidden", options["forbidden"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag imports matching any configured layer dependency specification."""
        yield from check_import_against_specs(
            self,
            node,
            self.forbidden,
            _format_layer_dependency_message,
        )


class ForbiddenConcreteImports(Rule):
    """CC701: Concrete infrastructure module imported inside domain paths.

    Simple single-layer configuration case built on the same module/path matching
    machinery as ``CC704``. Inert until ``forbidden_modules`` is configured.
    """

    code: ClassVar[str] = "CC701"
    message: ClassVar[str] = "Forbidden concrete module imported in domain code"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {
        NodeType.IMPORT_STATEMENT,
        NodeType.IMPORT_FROM_STATEMENT,
    }

    forbidden_modules: tuple[str, ...] = ()
    only_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.forbidden_modules = ()
        self.only_paths = ()
        self.exclude_paths = ()

    def _as_specs(self) -> tuple[LayerDependencySpec, ...]:
        if not self.forbidden_modules:
            return ()
        return (
            LayerDependencySpec(
                only_paths=self.only_paths,
                exclude_paths=self.exclude_paths,
                forbidden_modules=self.forbidden_modules,
            ),
        )

    def should_check_file(self, context: FileContext) -> bool:
        """Stay inert until ``forbidden_modules`` is set and *context* matches scope."""
        return any_spec_matches_file(context, self._as_specs())

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``forbidden_modules``, ``only_paths``, and ``exclude_paths``."""
        apply_str_list_options(
            self, options, "forbidden_modules", "only_paths", "exclude_paths"
        )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag imports matching ``forbidden_modules`` in scoped paths."""
        yield from check_import_against_specs(
            self,
            node,
            self._as_specs(),
            _format_layer_dependency_message,
        )


class ConcreteInstantiationInDomain(ScopedCallRule):
    """CC702: Concrete class instantiated directly inside configured domain paths.

    Inert until ``concrete_classes`` is configured. Exclude composition roots
    with ``exclude_paths``.
    """

    code: ClassVar[str] = "CC702"
    message: ClassVar[str] = "Concrete class instantiated directly in domain code"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CALL}
    target_option_name: ClassVar[str] = "concrete_classes"

    concrete_classes: tuple[str, ...] = ()

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``concrete_classes``, ``only_paths``, and ``exclude_paths``."""
        self._configure_scoped_call(options)

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag call nodes constructing any configured concrete class."""
        matched = self._matched_call_target(node)
        if matched is None:
            return
        yield self.diagnostic(
            node,
            f"Direct instantiation of concrete class '{matched}'; "
            "inject an abstraction via constructor or parameter instead",
        )


DEPENDENCY_RULES: list[type[Rule]] = [
    ForbiddenConcreteImports,
    ConcreteInstantiationInDomain,
    ForbiddenLayerDependency,
]

__all__ = [
    "DEPENDENCY_RULES",
    "ConcreteInstantiationInDomain",
    "ForbiddenConcreteImports",
    "ForbiddenLayerDependency",
]

"""Deterministic Clean Code rules for functions (CC101-CC104)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar

from rude.core.node_types import NodeType
from rude.providers import NO_SCOPE, Binding, ScopeProvider

from rude_clean_code._scope import ThresholdRule, definition_name, iter_own_scope

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import Diagnostic


def _is_local_binding(binding: Binding) -> bool:
    return not (binding.is_parameter or binding.is_global or binding.is_nonlocal)


def _count_own_scope_locals(node: Node) -> int:
    model = node.get_metadata(ScopeProvider).model
    scope_id = model.scope_at(node)
    if scope_id == NO_SCOPE or scope_id < 0 or scope_id >= len(model.scopes):
        return 0
    scope = model.scopes[scope_id]
    return sum(
        1
        for binding_id in scope.bindings.values()
        if _is_local_binding(model.bindings[binding_id])
    )


class FunctionTooLong(ThresholdRule):
    """CC101: Function exceeds maximum line count.

    Long functions usually do too many things at once and hide cohesive
    sub-operations behind local state.

    Configuration::

        [tool.rude.rules.CC101]
        max_lines = 30
    """

    code: ClassVar[str] = "CC101"
    message: ClassVar[str] = "Function exceeds maximum line count"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}
    option_name: ClassVar[str] = "max_lines"
    default_limit: ClassVar[int] = 30

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag function definitions spanning more lines than ``max_lines``."""
        lines = node.end_line - node.line + 1
        name = definition_name(node)
        msg = (
            f"Function '{name}' is too long ({lines} > {self.limit} lines); "
            "extract cohesive helper functions"
        )
        yield from self.emit_if_exceeds(node, lines, msg)


class TooManyParameters(ThresholdRule):
    """CC102: Function declares too many parameters.

    Wide parameter lists increase call-site coupling and often indicate missing
    domain abstractions such as dataclasses or value objects. Note that ``self``
    and ``cls`` are deliberately included in the parameter count.

    Configuration::

        [tool.rude.rules.CC102]
        max_parameters = 5
    """

    code: ClassVar[str] = "CC102"
    message: ClassVar[str] = "Function declares too many parameters"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}
    option_name: ClassVar[str] = "max_parameters"
    default_limit: ClassVar[int] = 5

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag functions declaring more parameters than ``max_parameters``."""
        count = node.parameter_count
        name = definition_name(node)
        msg = (
            f"Function '{name}' has too many parameters ({count} > {self.limit}); "
            "group related parameters into a parameter object or dataclass"
        )
        yield from self.emit_if_exceeds(node, count, msg)


class TooManyReturns(ThresholdRule):
    """CC103: Function has too many return statements.

    Excessive exit points in one function scope make data flow harder to trace
    unless separated into smaller helpers.

    Configuration::

        [tool.rude.rules.CC103]
        max_returns = 5
    """

    code: ClassVar[str] = "CC103"
    message: ClassVar[str] = "Function has too many return statements"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}
    option_name: ClassVar[str] = "max_returns"
    default_limit: ClassVar[int] = 5

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag functions with more own-scope ``return`` statements than ``max_returns``."""
        body = node.body
        if body is None:
            return
        returns = sum(
            1 for child in iter_own_scope(body) if child.type == "return_statement"
        )
        name = definition_name(node)
        msg = (
            f"Function '{name}' has too many return statements "
            f"({returns} > {self.limit}); simplify control flow or extract helpers"
        )
        yield from self.emit_if_exceeds(node, returns, msg)


class TooManyLocals(ThresholdRule):
    """CC104: Function binds too many local variables.

    Many distinct local bindings in a single function scope signal tangled state
    that belongs in smaller, single-purpose helpers.

    Configuration::

        [tool.rude.rules.CC104]
        max_locals = 10
    """

    code: ClassVar[str] = "CC104"
    message: ClassVar[str] = "Function binds too many local variables"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}
    metadata_dependencies: ClassVar[set[type]] = {ScopeProvider}
    option_name: ClassVar[str] = "max_locals"
    default_limit: ClassVar[int] = 10

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag functions binding more own-scope local variables than ``max_locals``."""
        locals_count = _count_own_scope_locals(node)
        name = definition_name(node)
        msg = (
            f"Function '{name}' has too many local variables "
            f"({locals_count} > {self.limit}); split cohesive steps into smaller functions"
        )
        yield from self.emit_if_exceeds(node, locals_count, msg)


FUNCTION_RULES: list[type[ThresholdRule]] = [
    FunctionTooLong,
    TooManyParameters,
    TooManyReturns,
    TooManyLocals,
]

__all__ = [
    "FUNCTION_RULES",
    "FunctionTooLong",
    "TooManyLocals",
    "TooManyParameters",
    "TooManyReturns",
]

"""Deterministic Clean Code rules for functions (CC101-CC104, CC107)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity
from rude.providers import NO_SCOPE, Binding, ScopeProvider

from rude_clean_code._scope import (
    ThresholdRule,
    definition_name,
    is_dunder,
    iter_own_scope,
    node_decorators,
    parse_str_list_option,
    unwrap_decorated,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.providers.semantic import SemanticModel

_DEF_TYPES = frozenset({"function_definition", "class_definition"})


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


def _iter_module_defs(module_node: Node) -> Iterator[Node]:
    stack = list(reversed(module_node.named_children))
    while stack:
        current = stack.pop()
        target = unwrap_decorated(current)
        if target.type in _DEF_TYPES:
            yield target
            continue
        stack.extend(reversed(current.named_children))


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


def _collect_module_used_names(model: SemanticModel) -> set[str]:
    module_id = model.module_scope
    used: set[str] = set()
    for scope_id, scope in enumerate(model.scopes):
        for use in scope.uses:
            if scope_id == module_id or not _is_shadowed(scope_id, use.name, model):
                used.add(use.name)
    return used


def _is_shadowed(scope_id: int, name: str, model: SemanticModel) -> bool:
    current = scope_id
    module_id = model.module_scope
    while (
        current != NO_SCOPE
        and current != module_id
        and 0 <= current < len(model.scopes)
    ):
        scope = model.scopes[current]
        if name in scope.bindings:
            binding = model.bindings[scope.bindings[name]]
            if not binding.is_global:
                return True
        current = scope.parent if scope.parent is not None else NO_SCOPE
    return False


class UnusedPrivateHelper(Rule):
    """CC107: Private module-level function or class is never referenced."""

    code: ClassVar[str] = "CC107"
    message: ClassVar[str] = "Private module-level helper is unused"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}
    metadata_dependencies: ClassVar[set[type]] = {ScopeProvider}

    ignore_decorators: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.ignore_decorators = ()

    def configure(self, options: dict[str, Any]) -> None:
        """Configure decorator names exempt from unused-private-helper reports."""
        if "ignore_decorators" in options:
            self.ignore_decorators = parse_str_list_option(
                self.code, "ignore_decorators", options["ignore_decorators"]
            )

    def _is_unused_private(
        self,
        defn: Node,
        model: SemanticModel,
        used_names: set[str],
        seen_bindings: set[int],
    ) -> bool:
        name = defn.name or ""
        if not name.startswith("_") or is_dunder(name):
            return False
        module_scope = model.scopes[model.module_scope]
        binding_id = module_scope.bindings.get(name)
        if binding_id is None or binding_id in seen_bindings:
            return False
        seen_bindings.add(binding_id)
        binding = model.bindings[binding_id]
        return not (binding.is_import or binding.is_used or name in used_names)

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag top-level ``_``-prefixed functions and classes unused in module scope."""
        model = node.get_metadata(ScopeProvider).model
        if model.module_scope == NO_SCOPE or model.module_scope >= len(model.scopes):
            return
        used_names = _collect_module_used_names(model)
        ignored = frozenset(self.ignore_decorators)
        seen_bindings: set[int] = set()
        for defn in _iter_module_defs(node):
            if not self._is_unused_private(defn, model, used_names, seen_bindings):
                continue
            if any(dec in ignored for dec in node_decorators(defn)):
                continue
            kind = "class" if defn.type == "class_definition" else "function"
            yield self.diagnostic(
                defn,
                f"Private {kind} '{defn.name}' is never used in this module; "
                "remove dead code or export it without a leading underscore",
            )


FUNCTION_RULES: list[type[Rule]] = [
    FunctionTooLong,
    TooManyParameters,
    TooManyReturns,
    TooManyLocals,
    UnusedPrivateHelper,
]

__all__ = [
    "FUNCTION_RULES",
    "FunctionTooLong",
    "TooManyLocals",
    "TooManyParameters",
    "TooManyReturns",
    "UnusedPrivateHelper",
]

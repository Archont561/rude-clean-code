"""Deterministic Clean Code rules for classes (CC201-CC202)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar

from rude.core.node_types import NodeType

from rude_clean_code._scope import ThresholdRule, definition_name

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import Diagnostic


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _direct_method_node(child: Node) -> Node | None:
    if child.type == "function_definition":
        return child
    if child.type == "decorated_definition":
        definition = child.child_by_field("definition")
        if definition is not None and definition.type == "function_definition":
            return definition
    return None


def _count_direct_methods(body: Node) -> tuple[int, int]:
    total = 0
    dunders = 0
    for child in body.named_children:
        method = _direct_method_node(child)
        if method is None:
            continue
        total += 1
        if _is_dunder(definition_name(method)):
            dunders += 1
    return total, dunders


class ClassTooLarge(ThresholdRule):
    """CC201: Class spans too many lines.

    Large classes tend to accumulate unrelated responsibilities. This size check
    serves as an early prompt to inspect cohesion.

    Configuration::

        [tool.rude.rules.CC201]
        max_lines = 200
    """

    code: ClassVar[str] = "CC201"
    message: ClassVar[str] = "Class spans too many lines"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CLASS_DEFINITION}
    option_name: ClassVar[str] = "max_lines"
    default_limit: ClassVar[int] = 200

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag class definitions spanning more lines than ``max_lines``."""
        lines = node.end_line - node.line + 1
        name = definition_name(node)
        msg = (
            f"Class '{name}' is too large ({lines} > {self.limit} lines); "
            "extract cohesive helper classes or modules"
        )
        yield from self.emit_if_exceeds(node, lines, msg)


class TooManyMethods(ThresholdRule):
    """CC202: Class defines too many direct methods.

    Classes exposing a large method surface often violate the Single
    Responsibility Principle. Dunder protocol methods are included in the total
    and counted separately in the diagnostic message for context.

    Configuration::

        [tool.rude.rules.CC202]
        max_methods = 15
    """

    code: ClassVar[str] = "CC202"
    message: ClassVar[str] = "Class defines too many direct methods"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CLASS_DEFINITION}
    option_name: ClassVar[str] = "max_methods"
    default_limit: ClassVar[int] = 15

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag classes defining more direct methods than ``max_methods``."""
        body = node.body
        if body is None:
            return
        total, dunders = _count_direct_methods(body)
        name = definition_name(node)
        msg = (
            f"Class '{name}' has too many methods "
            f"({total} > {self.limit}, including {dunders} dunder); "
            "extract cohesive collaborators or helper classes"
        )
        yield from self.emit_if_exceeds(node, total, msg)


CLASS_RULES: list[type[ThresholdRule]] = [
    ClassTooLarge,
    TooManyMethods,
]

__all__ = [
    "CLASS_RULES",
    "ClassTooLarge",
    "TooManyMethods",
]

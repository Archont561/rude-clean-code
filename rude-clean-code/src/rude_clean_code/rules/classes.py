"""Deterministic Clean Code rules for classes (CC201-CC202, CC207)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    ThresholdRule,
    base_candidate_names,
    definition_name,
    is_dunder,
    parse_nonneg_int,
    parse_str_list_option,
    unwrap_decorated,
)

if TYPE_CHECKING:
    from rude.core.node import Node


def _direct_method_node(child: Node) -> Node | None:
    target = unwrap_decorated(child)
    return target if target.type == "function_definition" else None


def _count_direct_methods(body: Node) -> tuple[int, int]:
    total = 0
    dunders = 0
    for child in body.named_children:
        method = _direct_method_node(child)
        if method is None:
            continue
        total += 1
        if is_dunder(definition_name(method)):
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


class TooManyBaseClasses(Rule):
    """CC207: Class inherits from too many direct base classes (excluding typing bases)."""

    code: ClassVar[str] = "CC207"
    message: ClassVar[str] = "Class inherits from too many direct base classes"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CLASS_DEFINITION}

    max_bases: int = 3
    ignore_bases: tuple[str, ...] = ("Generic", "Protocol")

    def __init__(self) -> None:
        self.max_bases = 3
        self.ignore_bases = ("Generic", "Protocol")

    def configure(self, options: dict[str, Any]) -> None:
        """Configure direct-base limit and exempt typing base names."""
        if "max_bases" in options:
            self.max_bases = parse_nonneg_int(
                self.code, "max_bases", options["max_bases"]
            )
        if "ignore_bases" in options:
            self.ignore_bases = parse_str_list_option(
                self.code, "ignore_bases", options["ignore_bases"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag classes with more non-ignored direct bases than ``max_bases``."""
        ignored = frozenset(self.ignore_bases)
        count = 0
        for base in node.bases:
            if base.type == "keyword_argument":
                continue
            if any(candidate in ignored for candidate in base_candidate_names(base)):
                continue
            count += 1
        if count > self.max_bases:
            name = definition_name(node)
            yield self.diagnostic(
                node,
                f"Class '{name}' inherits from too many direct base classes "
                f"({count} > {self.max_bases}); prefer composition over deep "
                "mixin inheritance",
            )


CLASS_RULES: list[type[Rule]] = [
    ClassTooLarge,
    TooManyMethods,
    TooManyBaseClasses,
]

__all__ = [
    "CLASS_RULES",
    "ClassTooLarge",
    "TooManyBaseClasses",
    "TooManyMethods",
]

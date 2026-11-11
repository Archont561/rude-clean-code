"""In-file SOLID and polymorphism indicator Clean Code rules (CC601)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    definition_name,
    iter_own_scope,
    parse_nonneg_int,
)

if TYPE_CHECKING:
    from rude.core.node import Node


def _is_isinstance_call(node: Node) -> bool:
    if node.type != "call":
        return False
    func = node.child_by_field("function")
    return func is not None and func.type == "identifier" and func.text == "isinstance"


def _compared_attribute_name(condition: Node | None) -> str | None:
    if condition is None:
        return None
    if condition.type == "parenthesized_expression" and condition.named_children:
        return _compared_attribute_name(condition.named_children[0])
    if condition.type != "comparison_operator":
        return None
    for child in condition.named_children:
        if child.type == "attribute":
            return child.text
    return None


def _dominant_elif_attribute(if_node: Node) -> tuple[str, int] | None:
    elifs = [child for child in if_node.named_children if child.type == "elif_clause"]
    if not elifs:
        return None
    conditions = [if_node.child_by_field("condition")] + [
        branch.child_by_field("condition") for branch in elifs
    ]
    attrs = [
        attr
        for cond in conditions
        if (attr := _compared_attribute_name(cond)) is not None
    ]
    if not attrs:
        return None
    return Counter(attrs).most_common(1)[0]


class RepeatedTypeSwitch(Rule):
    """CC601: Repeated ``isinstance`` checks or attribute-switching ``if``/``elif`` chain."""

    code: ClassVar[str] = "CC601"
    message: ClassVar[str] = (
        "Repeated type or attribute dispatch suggests missing polymorphism"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}

    min_isinstance: int = 3

    def __init__(self) -> None:
        self.min_isinstance = 3

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum check/branch threshold via ``min_isinstance``."""
        if "min_isinstance" in options:
            self.min_isinstance = parse_nonneg_int(
                self.code, "min_isinstance", options["min_isinstance"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag functions with repeated own-scope type or attribute switch dispatch."""
        body = node.body
        if body is None:
            return
        own_nodes = list(iter_own_scope(body))
        isinstance_count = sum(1 for child in own_nodes if _is_isinstance_call(child))
        if isinstance_count >= self.min_isinstance:
            name = definition_name(node)
            yield self.diagnostic(
                node,
                f"Function '{name}' makes {isinstance_count} (>= {self.min_isinstance}) "
                "isinstance() checks, indicating possible missing polymorphism or "
                "strategy dispatch (see also CC803)",
            )
        for child in own_nodes:
            if child.type != "if_statement":
                continue
            dominant = _dominant_elif_attribute(child)
            if dominant is None:
                continue
            attr, count = dominant
            if count >= self.min_isinstance:
                yield self.diagnostic(
                    child,
                    f"if/elif chain discriminates on attribute '{attr}' across "
                    f"{count} (>= {self.min_isinstance}) branches, indicating possible "
                    "missing polymorphism or strategy dispatch (see also CC803)",
                )


HEURISTIC_RULES: list[type[Rule]] = [RepeatedTypeSwitch]

__all__ = ["HEURISTIC_RULES", "RepeatedTypeSwitch"]

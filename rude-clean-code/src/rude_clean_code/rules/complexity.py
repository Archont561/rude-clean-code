"""Deterministic Clean Code rules for control complexity (CC301-CC303)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar

from rude.core.node_types import NodeType

from rude_clean_code._scope import (
    ThresholdRule,
    definition_name,
    iter_own_scope,
    max_own_scope_depth,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import Diagnostic

NESTING_NODE_TYPES: frozenset[str] = frozenset(
    {
        "if_statement",
        "for_statement",
        "while_statement",
        "try_statement",
        "with_statement",
        "match_statement",
    }
)

BRANCH_NODE_TYPES: frozenset[str] = frozenset(
    {
        "if_statement",
        "elif_clause",
        "for_statement",
        "while_statement",
        "boolean_operator",
        "conditional_expression",
        "case_clause",
    }
)


def _count_boolean_operands(node: Node) -> int:
    count = 0
    stack = [node]
    while stack:
        current = stack.pop()
        for field in ("left", "right"):
            operand = current.child_by_field(field)
            if operand is None:
                continue
            if operand.type == "boolean_operator":
                stack.append(operand)
            else:
                count += 1
    return count


class ExcessiveNesting(ThresholdRule):
    """CC301: Function exceeds maximum control-structure nesting depth.

    Deeply nested ``if``/``for``/``while``/``try``/``with``/``match`` blocks
    increase cognitive load; flattening with guard clauses and helper functions
    keeps intent obvious. Complements Rude's ``C901``.

    Configuration::

        [tool.rude.rules.CC301]
        max_depth = 4
    """

    code: ClassVar[str] = "CC301"
    message: ClassVar[str] = "Function exceeds maximum control nesting depth"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}
    option_name: ClassVar[str] = "max_depth"
    default_limit: ClassVar[int] = 4

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag functions whose deepest own-scope control nesting exceeds ``max_depth``."""
        body = node.body
        if body is None:
            return
        depth = max_own_scope_depth(body, NESTING_NODE_TYPES)
        name = definition_name(node)
        msg = (
            f"Function '{name}' has excessive nesting depth ({depth} > {self.limit}); "
            "use early returns or extract helpers"
        )
        yield from self.emit_if_exceeds(node, depth, msg)


class ExcessiveBooleanOperands(ThresholdRule):
    """CC302: Boolean expression combines too many operands.

    Long ``and``/``or`` chains encode compound predicates that read far better as
    named booleans or predicate helper functions. Complements Rude's ``C901``.

    Configuration::

        [tool.rude.rules.CC302]
        max_operands = 3
    """

    code: ClassVar[str] = "CC302"
    message: ClassVar[str] = "Boolean expression combines too many operands"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.BOOLEAN_OPERATOR}
    option_name: ClassVar[str] = "max_operands"
    default_limit: ClassVar[int] = 3

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag outermost boolean chains combining more than ``max_operands`` terms."""
        if node.parent_type == "boolean_operator":
            return
        operands = _count_boolean_operands(node)
        msg = (
            f"Boolean expression has too many operands ({operands} > {self.limit}); "
            "extract named predicate variables or helper functions"
        )
        yield from self.emit_if_exceeds(node, operands, msg)


class ExcessiveBranching(ThresholdRule):
    """CC303: Function contains too many decision points.

    Counts own-scope ``if``, ``elif``, ``for``, ``while``, ``and``/``or``,
    ternary expressions, and ``match`` cases. Intentionally distinct from and
    complementary to Rude's ``C901``.

    Configuration::

        [tool.rude.rules.CC303]
        max_branches = 10
    """

    code: ClassVar[str] = "CC303"
    message: ClassVar[str] = "Function contains too many decision points"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}
    option_name: ClassVar[str] = "max_branches"
    default_limit: ClassVar[int] = 10

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag functions with more own-scope decision points than ``max_branches``."""
        body = node.body
        if body is None:
            return
        branches = sum(
            1 for child in iter_own_scope(body) if child.type in BRANCH_NODE_TYPES
        )
        name = definition_name(node)
        msg = (
            f"Function '{name}' has too many branches ({branches} > {self.limit}); "
            "decompose conditional logic or use dispatch"
        )
        yield from self.emit_if_exceeds(node, branches, msg)


COMPLEXITY_RULES: list[type[ThresholdRule]] = [
    ExcessiveNesting,
    ExcessiveBooleanOperands,
    ExcessiveBranching,
]

__all__ = [
    "COMPLEXITY_RULES",
    "ExcessiveBooleanOperands",
    "ExcessiveBranching",
    "ExcessiveNesting",
]

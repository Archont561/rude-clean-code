"""Expression complexity and abstraction Clean Code heuristic rules (CC304-CC305)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    SCOPE_BOUNDARY_TYPES,
    base_candidate_names,
    parse_min_int,
    parse_nonneg_int,
)
from rude_clean_code.rules._parameter_analysis import (
    collect_module_classes,
    direct_class_methods,
)

if TYPE_CHECKING:
    from rude.core.node import Node

_EXPR_ROOT_PARENTS = frozenset(
    {
        "expression_statement",
        "assignment",
        "augmented_assignment",
        "return_statement",
        "if_statement",
        "elif_clause",
        "while_statement",
        "assert_statement",
        "yield",
        "raise_statement",
    }
)
_OPERATOR_NODE_KINDS = {
    "binary_operator": "binary",
    "boolean_operator": "bool",
    "comparison_operator": "cmp",
    "unary_operator": "unary",
    "not_operator": "bool",
    "conditional_expression": "ternary",
    "subscript": "subscript",
    "call": "call",
    "list_comprehension": "comp",
    "dictionary_comprehension": "comp",
    "set_comprehension": "comp",
    "generator_expression": "comp",
    "for_in_clause": "comp",
    "if_clause": "comp",
    "await": "await",
}
_DATA_CONTAINER_TYPES = frozenset({"list", "dictionary", "set", "tuple"})
_ABSTRACT_BASES = frozenset(
    {"ABC", "ABCMeta", "Protocol", "abc.ABC", "abc.ABCMeta", "typing.Protocol"}
)


def _is_candidate_expr_root(node: Node) -> bool:
    parent = node.parent
    if parent is None or parent.type not in _EXPR_ROOT_PARENTS:
        return False
    if parent.type == "assignment" and parent.child_by_field("left") == node:
        return False
    if node.type in _DATA_CONTAINER_TYPES:
        return False
    return node.type in _OPERATOR_NODE_KINDS


def _is_numeric_sign_unary(node: Node) -> bool:
    if node.type != "unary_operator":
        return False
    arg = node.child_by_field("argument")
    return arg is not None and arg.type in {"integer", "float"}


def _score_expression(expr: Node) -> tuple[int, int]:
    ops = 0
    kinds: set[str] = set()
    stack = [expr]
    while stack:
        current = stack.pop()
        if current != expr and current.type in SCOPE_BOUNDARY_TYPES:
            continue
        if (kind := _OPERATOR_NODE_KINDS.get(current.type)) is not None and not (
            _is_numeric_sign_unary(current)
        ):
            ops += 1
            kinds.add(kind)
        stack.extend(reversed(current.named_children))
    return ops, len(kinds)


def _is_visible_abstract_or_protocol(cls_node: Node) -> bool:
    for base in cls_node.bases:
        if base.type == "keyword_argument":
            val = base.child_by_field("value")
            if val is not None and val.text in _ABSTRACT_BASES:
                return True
            continue
        if any(c in _ABSTRACT_BASES for c in base_candidate_names(base)):
            return True
    for _method, decs in direct_class_methods(cls_node):
        if "abstractmethod" in decs:
            return True
    return False


def _subclass_names(classes: dict[str, Node], base_name: str) -> list[str]:
    result: list[str] = []
    for cls_name, cls_node in classes.items():
        if cls_name == base_name:
            continue
        for base in cls_node.bases:
            if base.type == "keyword_argument":
                continue
            if base_name in base_candidate_names(base):
                result.append(cls_name)
                break
    return result


def _count_external_consumers(
    module_node: Node,
    base_name: str,
    base_node: Node,
    subclass_nodes: list[Node],
) -> int:
    excluded_spans = [(base_node.start_byte, base_node.end_byte)]
    for sub in subclass_nodes:
        superclasses = sub.child_by_field("superclasses")
        if superclasses is not None:
            excluded_spans.append((superclasses.start_byte, superclasses.end_byte))
    uses = 0
    for node in module_node.walk():
        if node.type != "identifier" or node.text != base_name:
            continue
        if any(s <= node.start_byte <= e for s, e in excluded_spans):
            continue
        uses += 1
    return uses


class ComplexExpression(Rule):
    """CC304: Single expression combines too many operators, calls, or comprehensions."""

    code: ClassVar[str] = "CC304"
    message: ClassVar[str] = "Expression combines too many operators and calls"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    max_operators: int = 8

    def __init__(self) -> None:
        self.max_operators = 8

    def configure(self, options: dict[str, Any]) -> None:
        """Configure maximum expression complexity budget via ``max_operators``."""
        if "max_operators" in options:
            self.max_operators = parse_nonneg_int(
                self.code, "max_operators", options["max_operators"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag outermost expressions combining multiple operator kinds above limit."""
        skip_until = -1
        for current in node.walk():
            if current.start_byte < skip_until or not _is_candidate_expr_root(current):
                continue
            ops, kind_count = _score_expression(current)
            skip_until = current.end_byte
            if ops > self.max_operators and kind_count >= 2:
                yield self.diagnostic(
                    current,
                    f"Expression combines {ops} > {self.max_operators} operators/calls "
                    f"across {kind_count} construct kinds; consider extracting named "
                    "intermediate variables or helper functions",
                )


class UnnecessaryAbstraction(Rule):
    """CC305: Visible abstract base or Protocol has only one in-file implementation."""

    code: ClassVar[str] = "CC305"
    message: ClassVar[str] = (
        "Abstract base or protocol has only one in-file implementation"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    min_consumers: int = 2

    def __init__(self) -> None:
        self.min_consumers = 2

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum in-file consumer count via ``min_consumers``."""
        if "min_consumers" in options:
            self.min_consumers = parse_min_int(
                self.code, "min_consumers", options["min_consumers"], 1
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Suggest simplifying single-impl visible abstractions with low in-file usage."""
        classes = collect_module_classes(node)
        for base_name, base_node in classes.items():
            if not _is_visible_abstract_or_protocol(base_node):
                continue
            sub_names = _subclass_names(classes, base_name)
            if len(sub_names) != 1:
                continue
            other_uses = _count_external_consumers(
                node, base_name, base_node, [classes[s] for s in sub_names]
            )
            consumers = 1 + other_uses
            if consumers < self.min_consumers:
                yield self.diagnostic(
                    base_node,
                    f"Abstract class or Protocol '{base_name}' has 1 in-file "
                    f"implementation ('{sub_names[0]}') and {other_uses} other in-file "
                    f"references ({consumers} < {self.min_consumers}); cross-file usage "
                    "is outside per-file scope — consider removing speculative abstraction",
                )


def _is_negated_condition(cond: Node | None) -> bool:
    while cond is not None and cond.type == "parenthesized_expression":
        cond = cond.named_children[0] if cond.named_children else None
    if cond is None:
        return False
    if cond.type == "not_operator":
        return True
    if cond.type == "comparison_operator":
        return any(child.type == "!=" for child in cond.children)
    return False


class InvertedConditional(Rule):
    """CC307: ``if``/``else`` branch puts a negated condition ahead of its ``else``."""

    code: ClassVar[str] = "CC307"
    message: ClassVar[str] = (
        "Negated condition with else branch may read more clearly inverted"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.IF_STATEMENT}

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag pure two-branch ``if``/``else`` statements using negated conditions."""
        has_else = False
        for child in node.named_children:
            if child.type == "elif_clause":
                return
            if child.type == "else_clause":
                has_else = True
        if not has_else:
            return
        if _is_negated_condition(node.child_by_field("condition")):
            yield self.diagnostic(
                node,
                "Conditional uses a negated check ('not' or '!=') with an 'else' "
                "branch; consider inverting to handle the positive case first",
            )


COMPLEXITY_HEURISTIC_RULES: list[type[Rule]] = [
    ComplexExpression,
    UnnecessaryAbstraction,
    InvertedConditional,
]

__all__ = [
    "COMPLEXITY_HEURISTIC_RULES",
    "ComplexExpression",
    "InvertedConditional",
    "UnnecessaryAbstraction",
]

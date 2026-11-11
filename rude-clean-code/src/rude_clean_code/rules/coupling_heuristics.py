"""Law of Demeter and external private-member access rules (CC604-CC605)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    is_dunder,
    is_test_context,
    parse_bool_option,
    parse_nonneg_int,
    parse_str_list_option,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

_CHAIN_NODES = frozenset({"attribute", "call"})
_IGNORED_CONTEXTS = frozenset({"import_statement", "import_from_statement", "type"})


def _in_ignored_context(node: Node) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.type in _IGNORED_CONTEXTS:
            return True
        parent = parent.parent
    return False


def _is_outermost_chain(node: Node) -> bool:
    parent = node.parent
    if parent is None:
        return True
    if parent.type == "attribute" and parent.child_by_field("object") == node:
        return False
    return not (parent.type == "call" and parent.child_by_field("function") == node)


def _count_chain_hops(node: Node) -> int:
    hops = 0
    current: Node | None = node
    while current is not None:
        if current.type == "attribute":
            hops += 1
            current = current.child_by_field("object")
        elif current.type == "call":
            current = current.child_by_field("function")
        elif current.type == "parenthesized_expression" and current.named_children:
            current = current.named_children[0]
        else:
            break
    return hops


def _is_self_cls_or_super(receiver: Node | None) -> bool:
    if receiver is None:
        return False
    if receiver.type == "identifier":
        return receiver.text in {"self", "cls"}
    if receiver.type == "call":
        callee = receiver.child_by_field("function")
        return (
            callee is not None
            and callee.type == "identifier"
            and callee.text == "super"
        )
    return False


class ChainedAccess(Rule):
    """CC604: Long single-line attribute or call chain (Law of Demeter indicator)."""

    code: ClassVar[str] = "CC604"
    message: ClassVar[str] = "Chained attribute or call access exceeds depth threshold"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.ATTRIBUTE, NodeType.CALL}

    max_chain_depth: int = 3
    allowed_prefixes: tuple[str, ...] = ("self.",)
    ignore_multiline: bool = True

    def __init__(self) -> None:
        self.max_chain_depth = 3
        self.allowed_prefixes = ("self.",)
        self.ignore_multiline = True

    def configure(self, options: dict[str, Any]) -> None:
        """Configure chain hop budget, allowed receiver prefixes, and multiline exemption."""
        if "max_chain_depth" in options:
            self.max_chain_depth = parse_nonneg_int(
                self.code, "max_chain_depth", options["max_chain_depth"]
            )
        if "allowed_prefixes" in options:
            self.allowed_prefixes = parse_str_list_option(
                self.code, "allowed_prefixes", options["allowed_prefixes"]
            )
        if "ignore_multiline" in options:
            self.ignore_multiline = parse_bool_option(
                self.code, "ignore_multiline", options["ignore_multiline"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag outermost chains exceeding ``max_chain_depth`` hops."""
        if not _is_outermost_chain(node) or _in_ignored_context(node):
            return
        if self.ignore_multiline and node.end_line > node.line:
            return
        text = " ".join(node.text.split())
        if any(text.startswith(prefix) for prefix in self.allowed_prefixes if prefix):
            return
        hops = _count_chain_hops(node)
        if hops > self.max_chain_depth:
            yield self.diagnostic(
                node,
                f"Chained access depth ({hops} > {self.max_chain_depth} hops) suggests "
                "tight structural coupling; consider Law of Demeter delegation or "
                "intermediate names",
            )


class ExternalPrivateAccess(Rule):
    """CC605: Reading or mutating a ``_private`` member on an external receiver."""

    code: ClassVar[str] = "CC605"
    message: ClassVar[str] = (
        "Accesses single-underscore private member on external object"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.ATTRIBUTE}

    exclude_tests: bool = True
    allowed_members: tuple[str, ...] = ("_asdict", "_replace", "_make")

    def __init__(self) -> None:
        self.exclude_tests = True
        self.allowed_members = ("_asdict", "_replace", "_make")

    def should_check_file(self, context: FileContext) -> bool:
        """Skip test modules unless ``exclude_tests`` is disabled."""
        return not (self.exclude_tests and is_test_context(context))

    def configure(self, options: dict[str, Any]) -> None:
        """Configure test-file exclusion and exempt protocol attribute names."""
        if "exclude_tests" in options:
            self.exclude_tests = parse_bool_option(
                self.code, "exclude_tests", options["exclude_tests"]
            )
        if "allowed_members" in options:
            self.allowed_members = parse_str_list_option(
                self.code, "allowed_members", options["allowed_members"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag ``obj._member`` accesses outside ``self``, ``cls``, or ``super()``."""
        attr = node.child_by_field("attribute")
        if attr is None or not attr.text:
            return
        name = attr.text
        if not name.startswith("_") or name == "_" or is_dunder(name):
            return
        if name in self.allowed_members:
            return
        if _is_self_cls_or_super(node.child_by_field("object")):
            return
        yield self.diagnostic(
            node,
            f"External access to private member '{name}' suggests coupling to "
            "internal implementation details; prefer a public method or property",
        )


COUPLING_HEURISTIC_RULES: list[type[Rule]] = [
    ChainedAccess,
    ExternalPrivateAccess,
]

__all__ = [
    "COUPLING_HEURISTIC_RULES",
    "ChainedAccess",
    "ExternalPrivateAccess",
]

"""Shared own-scope AST traversal and threshold rule base helpers."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

if TYPE_CHECKING:
    from rude.core.node import Node

SCOPE_BOUNDARY_TYPES: frozenset[str] = frozenset(
    {
        "function_definition",
        "class_definition",
        "lambda",
    }
)


def definition_name(node: Node) -> str:
    """Return the readable name of a function or class definition node."""
    return node.name or "<anonymous>"


def iter_own_scope(root: Node) -> Iterator[Node]:
    """Yield own-scope descendants without entering nested functions, classes, or lambdas."""
    stack = list(reversed(root.named_children))
    while stack:
        current = stack.pop()
        if current.type in SCOPE_BOUNDARY_TYPES:
            continue
        yield current
        stack.extend(reversed(current.named_children))


def max_own_scope_depth(root: Node, control_types: frozenset[str]) -> int:
    """Return maximum nesting depth of *control_types* in *root*'s own scope."""
    max_depth = 0
    stack: list[tuple[Node, int]] = [
        (child, 0) for child in reversed(root.named_children)
    ]
    while stack:
        current, depth = stack.pop()
        if current.type in SCOPE_BOUNDARY_TYPES:
            continue
        next_depth = depth + 1 if current.type in control_types else depth
        max_depth = max(max_depth, next_depth)
        stack.extend((child, next_depth) for child in reversed(current.named_children))
    return max_depth


class ThresholdRule(Rule):
    """Base class for deterministic rules governed by one non-negative integer limit."""

    severity: ClassVar[Severity | None] = Severity.WARNING
    option_name: ClassVar[str]
    default_limit: ClassVar[int]

    def __init__(self) -> None:
        setattr(self, self.option_name, self.default_limit)

    @property
    def limit(self) -> int:
        """Configured upper bound (inclusive) for this rule."""
        return int(getattr(self, self.option_name))

    def configure(self, options: dict[str, Any]) -> None:
        """Validate and apply the configured threshold from ``[tool.rude.rules.<CODE>]``."""
        if self.option_name not in options:
            return
        raw = options[self.option_name]
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
            msg = (
                f"{self.code} option '{self.option_name}' must be a "
                f"non-negative integer, got {raw!r}"
            )
            raise ValueError(msg)
        setattr(self, self.option_name, raw)

    def emit_if_exceeds(
        self,
        node: Node,
        measured: int,
        message: str,
    ) -> Iterator[Diagnostic]:
        """Yield a diagnostic on *node* when *measured* exceeds the configured limit."""
        if measured > self.limit:
            yield self.diagnostic(node, message)

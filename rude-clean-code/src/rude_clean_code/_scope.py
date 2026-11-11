"""Shared own-scope AST traversal, option parsing, and rule base helpers."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

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


def is_dunder(name: str) -> bool:
    """Return whether *name* is a double-underscore Python dunder identifier."""
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def unwrap_decorated(node: Node) -> Node:
    """Return the underlying definition when *node* is a ``decorated_definition``."""
    if node.type != "decorated_definition":
        return node
    inner = node.child_by_field("definition")
    if inner is not None:
        return inner
    for child in node.named_children:
        if child.type != "decorator":
            return child
    return node


def _decorator_target_names(decorator: Node) -> Iterator[str]:
    for child in decorator.named_children:
        target = child.child_by_field("function") if child.type == "call" else child
        if target is None:
            continue
        text = target.text
        if text:
            yield text
            if "." in text:
                yield text.rsplit(".", maxsplit=1)[-1]


def node_decorators(node: Node) -> list[str]:
    """Return normalized decorator names attached to *node*'s ``decorated_definition``."""
    parent = node.parent
    if parent is None or parent.type != "decorated_definition":
        return []
    names: list[str] = []
    for child in parent.named_children:
        if child.type == "decorator":
            names.extend(_decorator_target_names(child))
    return names


def base_candidate_names(base: Node) -> tuple[str, ...]:
    """Return full and short candidate names for a class inheritance base node."""
    target = base.child_by_field("value") if base.type == "subscript" else base
    if target is None:
        return ()
    text = target.text
    if not text:
        return ()
    if "." in text:
        return (text, text.rsplit(".", maxsplit=1)[-1])
    return (text,)


def is_module_level_definition(node: Node) -> bool:
    """Return whether *node* sits directly at module top level (optionally decorated)."""
    parent = node.parent
    if parent is None:
        return False
    if parent.type == "decorated_definition":
        parent = parent.parent
    return parent is not None and parent.type == "module"


def is_test_context(context: FileContext) -> bool:
    """Return whether *context* points to a test module or file inside a test folder."""
    if context.is_test_file() or context.path.stem == "conftest":
        return True
    parent_parts = set(context.path.parts[:-1])
    return "tests" in parent_parts or "test" in parent_parts


def matches_path_patterns(
    context: FileContext,
    patterns: Sequence[str],
) -> bool:
    """Return whether *context* matches any configured path fragment or glob."""
    normalized = tuple(pattern.replace("\\", "/") for pattern in patterns if pattern)
    if not normalized:
        return False
    posix = context.path.as_posix()
    if context.is_in_path(*normalized):
        return True
    for pattern in normalized:
        if fnmatch(posix, pattern):
            return True
        if not pattern.startswith(("/", "*")) and fnmatch(posix, f"*/{pattern}"):
            return True
    return False


def matches_exclude_paths(
    context: FileContext,
    patterns: tuple[str, ...],
) -> bool:
    """Return whether *context* matches any excluded path fragment or glob."""
    return matches_path_patterns(context, patterns)


def _option_error(
    code: str,
    option_name: str,
    expected: str,
    raw: object,
) -> ValueError:
    return ValueError(f"{code} option '{option_name}' must be {expected}, got {raw!r}")


def parse_nonneg_int(code: str, option_name: str, raw: object) -> int:
    """Validate a non-negative integer rule option."""
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise _option_error(code, option_name, "a non-negative integer", raw)
    return raw


def parse_bool_option(code: str, option_name: str, raw: object) -> bool:
    """Validate a boolean rule option."""
    if not isinstance(raw, bool):
        raise _option_error(code, option_name, "a boolean", raw)
    return raw


def parse_str_list_option(
    code: str,
    option_name: str,
    raw: object,
) -> tuple[str, ...]:
    """Validate a list/tuple-of-strings rule option and freeze it into a tuple."""
    if not isinstance(raw, (list, tuple)) or any(
        not isinstance(item, str) for item in raw
    ):
        raise _option_error(code, option_name, "a list of strings", raw)
    return tuple(raw)


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
        value = parse_nonneg_int(self.code, self.option_name, options[self.option_name])
        setattr(self, self.option_name, value)

    def emit_if_exceeds(
        self,
        node: Node,
        measured: int,
        message: str,
    ) -> Iterator[Diagnostic]:
        """Yield a diagnostic on *node* when *measured* exceeds the configured limit."""
        if measured > self.limit:
            yield self.diagnostic(node, message)

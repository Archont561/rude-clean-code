"""In-file naming and magic-literal Clean Code rules (CC401-CC403)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity
from rude.utils import extract_string_content

from rude_clean_code._scope import (
    SCOPE_BOUNDARY_TYPES,
    definition_name,
    is_dunder,
    parse_nonneg_int,
    parse_str_list_option,
)

if TYPE_CHECKING:
    from rude.core.node import Node

DEFAULT_VAGUE_NAMES: frozenset[str] = frozenset(
    {
        "data",
        "do_stuff",
        "do_work",
        "fn",
        "func",
        "handle",
        "helper",
        "helpers",
        "info",
        "item",
        "items",
        "manage",
        "misc",
        "obj",
        "process",
        "stuff",
        "temp",
        "thing",
        "things",
        "tmp",
        "util",
        "utils",
        "val",
        "value",
    }
)

_TYPE_LITERAL_CONTAINERS = frozenset(
    {"Annotated", "Literal", "typing.Annotated", "typing.Literal"}
)
_TRIVIAL_NUMBERS = {0, 1, -1}


def _is_vague_identifier(name: str, vague_names: frozenset[str]) -> bool:
    if not name or name == "_" or is_dunder(name):
        return False
    stripped = name.strip("_")
    if not stripped:
        return False
    return len(stripped) == 1 or stripped.lower() in vague_names


def _enclosing_scope_node(node: Node) -> Node | None:
    parent = node.parent
    while parent is not None:
        if parent.type in SCOPE_BOUNDARY_TYPES:
            return parent
        parent = parent.parent
    return None


def _is_docstring_node(str_node: Node) -> bool:
    stmt = str_node.parent
    if stmt is None or stmt.type != "expression_statement":
        return False
    parent = stmt.parent
    if parent is None:
        return False
    if parent.type == "module":
        return (
            next((c for c in parent.named_children if c.type != "comment"), None)
            == stmt
        )
    if parent.type == "block" and parent.parent_type in {
        "function_definition",
        "class_definition",
    }:
        return (
            next((c for c in parent.named_children if c.type != "comment"), None)
            == stmt
        )
    return False


def _is_cast_type_arg(call_node: Node, target_node: Node) -> bool:
    func = call_node.child_by_field("function")
    if func is None or func.text not in {"cast", "typing.cast"}:
        return False
    args = call_node.call_arguments
    if not args:
        return False
    return args[0].start_byte <= target_node.start_byte <= args[0].end_byte


def _is_in_type_context(node: Node) -> bool:
    current = node.parent
    while current is not None:
        if current.type == "type":
            return True
        if current.type == "subscript":
            target = current.child_by_field("value")
            if target is not None and target.text in _TYPE_LITERAL_CONTAINERS:
                return True
        if current.type == "call" and _is_cast_type_arg(current, node):
            return True
        current = current.parent
    return False


def _parse_numeric_literal(
    text: str, *, negative: bool = False
) -> tuple[str, int | float] | None:
    cleaned = text.replace("_", "")
    try:
        int_val = int(cleaned, 0)
        numeric_val: int | float = -int_val if negative else int_val
        return ("num", numeric_val)
    except ValueError:
        try:
            float_val = float(cleaned)
            signed_float = -float_val if negative else float_val
            return ("num", signed_float)
        except ValueError:
            return None


def _string_literal_entry(node: Node) -> tuple[tuple[str, str], str] | None:
    if _is_docstring_node(node) or _is_in_type_context(node):
        return None
    if any(child.type == "interpolation" for child in node.named_children):
        return None
    content = extract_string_content(node.text)
    if content is None or content == "":
        return None
    return ("str", content), node.text


def _unary_numeric_entry(node: Node) -> tuple[tuple[str, int | float], str] | None:
    if not any(child.type == "-" for child in node.children):
        return None
    arg = node.child_by_field("argument")
    if arg is None or arg.type not in {"integer", "float"}:
        return None
    parsed = _parse_numeric_literal(arg.text, negative=True)
    if parsed is None or parsed[1] in _TRIVIAL_NUMBERS:
        return None
    return parsed, node.text


def _collect_magic_literals(
    module_node: Node,
) -> dict[tuple[str, object], tuple[Node, str, int]]:
    counts: dict[tuple[str, object], int] = defaultdict(int)
    first_seen: dict[tuple[str, object], tuple[Node, str]] = {}
    skip_bytes: set[tuple[int, int]] = set()
    for node in module_node.walk():
        span = (node.start_byte, node.end_byte)
        if span in skip_bytes:
            continue
        entry: tuple[tuple[str, Any], str] | None = None
        if node.type == "unary_operator":
            entry = _unary_numeric_entry(node)
            arg = node.child_by_field("argument")
            if arg is not None and arg.type in {"integer", "float"}:
                skip_bytes.add((arg.start_byte, arg.end_byte))
        elif node.type in {"integer", "float"}:
            parsed = _parse_numeric_literal(node.text)
            if parsed is not None and parsed[1] not in _TRIVIAL_NUMBERS:
                entry = parsed, node.text
        elif node.type == "string":
            entry = _string_literal_entry(node)
        if entry is None:
            continue
        key, label = entry
        counts[key] += 1
        first_seen.setdefault(key, (node, label))
    return {key: (*first_seen[key], count) for key, count in counts.items()}


class UnclearFunctionName(Rule):
    """CC401: Function name is single-letter or in the extendable vague-name list."""

    code: ClassVar[str] = "CC401"
    message: ClassVar[str] = "Function name is vague or overly generic"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}

    vague_names: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.vague_names = ()

    def configure(self, options: dict[str, Any]) -> None:
        """Extend (never shrink) the built-in vague-name vocabulary."""
        if "vague_names" in options:
            self.vague_names = parse_str_list_option(
                self.code, "vague_names", options["vague_names"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag unclear or single-letter function names, exempting dunders."""
        name = definition_name(node)
        vocab = DEFAULT_VAGUE_NAMES | frozenset(
            item.lower() for item in self.vague_names
        )
        if _is_vague_identifier(name, vocab):
            yield self.diagnostic(
                node,
                f"Function name '{name}' appears vague or generic; consider a "
                "more descriptive domain-specific name",
            )


class UnclearClassOrVariableName(Rule):
    """CC402: Class name or non-short-scope variable name is vague or single-letter."""

    code: ClassVar[str] = "CC402"
    message: ClassVar[str] = "Class or variable name is vague or overly generic"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    vague_names: tuple[str, ...] = ()
    max_short_scope: int = 5

    def __init__(self) -> None:
        self.vague_names = ()
        self.max_short_scope = 5

    def configure(self, options: dict[str, Any]) -> None:
        """Extend the vague-name list and configure ``max_short_scope``."""
        if "vague_names" in options:
            self.vague_names = parse_str_list_option(
                self.code, "vague_names", options["vague_names"]
            )
        if "max_short_scope" in options:
            self.max_short_scope = parse_nonneg_int(
                self.code, "max_short_scope", options["max_short_scope"]
            )

    def _check_assignment(
        self,
        node: Node,
        vocab: frozenset[str],
    ) -> Diagnostic | None:
        left = node.child_by_field("left")
        if left is None or left.type != "identifier":
            return None
        scope = _enclosing_scope_node(node)
        is_annotated = node.child_by_field("type") is not None
        in_short_scope = (
            scope is not None
            and (scope.end_line - scope.line + 1) <= self.max_short_scope
        )
        if scope is not None and (not is_annotated or in_short_scope):
            return None
        if not _is_vague_identifier(left.text, vocab):
            return None
        return self.diagnostic(
            left,
            f"Identifier '{left.text}' appears vague or overly generic; "
            "consider a more descriptive name",
        )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag unclear class names and module-level or annotated variable names."""
        vocab = DEFAULT_VAGUE_NAMES | frozenset(
            item.lower() for item in self.vague_names
        )
        for current in node.walk():
            if current.type == "class_definition":
                name = definition_name(current)
                if _is_vague_identifier(name, vocab):
                    yield self.diagnostic(
                        current,
                        f"Class name '{name}' appears vague or generic; consider "
                        "a more specific domain noun",
                    )
            elif current.type in {"assignment", "augmented_assignment"}:
                diag = self._check_assignment(current, vocab)
                if diag is not None:
                    yield diag


class RepeatedMagicLiteral(Rule):
    """CC403: Non-trivial numeric or string literal repeated across one file."""

    code: ClassVar[str] = "CC403"
    message: ClassVar[str] = "Non-trivial literal is repeated without a named constant"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    min_occurrences: int = 3

    def __init__(self) -> None:
        self.min_occurrences = 3

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum repeat threshold (>= 1) via ``min_occurrences``."""
        if "min_occurrences" in options:
            value = parse_nonneg_int(
                self.code, "min_occurrences", options["min_occurrences"]
            )
            if value < 1:
                msg = (
                    f"{self.code} option 'min_occurrences' must be at least 1, "
                    f"got {value!r}"
                )
                raise ValueError(msg)
            self.min_occurrences = value

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag non-trivial literals appearing at least ``min_occurrences`` times."""
        for first_node, label, count in _collect_magic_literals(node).values():
            if count >= self.min_occurrences:
                yield self.diagnostic(
                    first_node,
                    f"Magic literal {label} appears {count} times "
                    f"(>= {self.min_occurrences}) in this file; extract a named constant",
                )


NAMING_RULES: list[type[Rule]] = [
    UnclearFunctionName,
    UnclearClassOrVariableName,
    RepeatedMagicLiteral,
]

__all__ = [
    "DEFAULT_VAGUE_NAMES",
    "NAMING_RULES",
    "RepeatedMagicLiteral",
    "UnclearClassOrVariableName",
    "UnclearFunctionName",
]

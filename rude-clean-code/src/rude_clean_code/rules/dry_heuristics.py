"""In-file repeated validation and constant-definition DRY rules (CC503-CC504)."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity
from rude.utils import extract_string_content

from rude_clean_code._scope import (
    definition_name,
    iter_own_scope,
    parse_min_int,
)
from rude_clean_code.rules._parameter_analysis import (
    body_statements,
    parse_parameters,
)

if TYPE_CHECKING:
    from rude.core.node import Node

_TRIVIAL_CONSTANTS = {0, 1, -1}
_EXIT_TYPES = frozenset({"raise_statement", "return_statement"})


def _param_aliases(func_node: Node) -> dict[str, str]:
    names = [
        spec.name
        for spec in parse_parameters(func_node)
        if not spec.is_variadic and spec.name not in {"self", "cls"}
    ]
    return {name: f"<PARAM_{idx}>" for idx, name in enumerate(names)}


def _has_elif_or_else(if_node: Node) -> bool:
    return any(
        child.type in {"elif_clause", "else_clause"} for child in if_node.named_children
    )


def _is_guard_block(block: Node | None) -> bool:
    if block is None or block.type != "block":
        return False
    stmts = [c for c in block.named_children if c.type != "comment"]
    return bool(stmts) and stmts[-1].type in _EXIT_TYPES


def _normalize_text(node: Node, aliases: dict[str, str]) -> str:
    text = " ".join(node.text.split())
    for name, placeholder in sorted(aliases.items(), key=lambda p: -len(p[0])):
        text = re.sub(rf"\b{re.escape(name)}\b", placeholder, text)
    return text


def _guard_statement_signature(
    stmt: Node, aliases: dict[str, str]
) -> tuple[str, bool] | None:
    if stmt.type != "if_statement" or _has_elif_or_else(stmt):
        return None
    cond = stmt.child_by_field("condition")
    consequence = stmt.child_by_field("consequence")
    if cond is None or not _is_guard_block(consequence):
        return None
    normalized = _normalize_text(stmt, aliases)
    if "<PARAM_" not in normalized:
        return None
    has_compound = any(desc.type == "boolean_operator" for desc in iter_own_scope(cond))
    return normalized, has_compound


def _validation_signature(func_node: Node) -> str | None:
    body = func_node.body
    if body is None:
        return None
    aliases = _param_aliases(func_node)
    if not aliases:
        return None
    guards: list[str] = []
    has_compound = False
    for stmt in body_statements(body):
        entry = _guard_statement_signature(stmt, aliases)
        if entry is None:
            break
        normalized, compound = entry
        has_compound = has_compound or compound
        guards.append(normalized)
    if len(guards) < 2 and not has_compound:
        return None
    return "\n".join(guards)


def _parse_numeric_key(text: str, *, negative: bool = False) -> int | float | None:
    cleaned = text.replace("_", "")
    try:
        val = int(cleaned, 0)
        return -val if negative else val
    except ValueError:
        try:
            fval = float(cleaned)
            return -fval if negative else fval
        except ValueError:
            return None


def _numeric_literal_key(
    node: Node, *, negative: bool
) -> tuple[tuple[str, object], str] | None:
    target = node.child_by_field("argument") if negative else node
    if target is None or target.type not in {"integer", "float"}:
        return None
    num = _parse_numeric_key(target.text, negative=negative)
    if num is None or num in _TRIVIAL_CONSTANTS:
        return None
    return ("num", num), node.text


def _constant_literal_key(node: Node) -> tuple[tuple[str, object], str] | None:
    if node.type == "unary_operator" and any(c.type == "-" for c in node.children):
        return _numeric_literal_key(node, negative=True)
    if node.type in {"integer", "float"}:
        return _numeric_literal_key(node, negative=False)
    if node.type == "string":
        if any(c.type == "interpolation" for c in node.named_children):
            return None
        content = extract_string_content(node.text)
        if content:
            return ("str", content), node.text
    return None


def _is_constant_identifier(name: str) -> bool:
    return name != "__all__" and name.isupper() and any(ch.isalpha() for ch in name)


class RepeatedValidation(Rule):
    """CC503: Structurally similar parameter validation guards across multiple functions."""

    code: ClassVar[str] = "CC503"
    message: ClassVar[str] = "Repeated parameter validation logic across functions"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    min_functions: int = 3

    def __init__(self) -> None:
        self.min_functions = 3

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum matching functions (>= 2) via ``min_functions``."""
        if "min_functions" in options:
            self.min_functions = parse_min_int(
                self.code, "min_functions", options["min_functions"], 2
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag repeated leading validation guard sequences in one module."""
        groups: dict[str, list[tuple[Node, str]]] = defaultdict(list)
        for fn in node.find("function_definition"):
            sig = _validation_signature(fn)
            if sig is not None:
                groups[sig].append((fn, definition_name(fn)))
        for matches in groups.values():
            if len(matches) < self.min_functions:
                continue
            first_node, _first_name = matches[0]
            locations = ", ".join(f"'{name}' (line {fn.line})" for fn, name in matches)
            yield self.diagnostic(
                first_node,
                f"Validation guard sequence is repeated across {len(matches)} >= "
                f"{self.min_functions} functions in this file ({locations}); "
                "suggests extracting a shared validator helper",
            )


def _collect_module_constants(
    module_node: Node,
) -> dict[tuple[str, object], list[tuple[Node, str, str]]]:
    groups: dict[tuple[str, object], list[tuple[Node, str, str]]] = defaultdict(list)
    for stmt in module_node.named_children:
        if stmt.type != "expression_statement" or not stmt.named_children:
            continue
        assign = stmt.named_children[0]
        if assign.type != "assignment":
            continue
        left = assign.child_by_field("left")
        right = assign.child_by_field("right")
        is_valid_left = (
            left is not None
            and left.type == "identifier"
            and _is_constant_identifier(left.text)
        )
        if not is_valid_left or right is None or left is None:
            continue
        entry = _constant_literal_key(right)
        if entry is not None:
            key, label = entry
            groups[key].append((left, left.text, label))
    return groups


class RepeatedConstantDefinition(Rule):
    """CC504: File-scope subset flagging differently named constants sharing a literal."""

    code: ClassVar[str] = "CC504"
    message: ClassVar[str] = (
        "Same non-trivial literal assigned to multiple constants in this file"
    )
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    min_occurrences: int = 3

    def __init__(self) -> None:
        self.min_occurrences = 3

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum distinct-constant occurrences (>= 2)."""
        if "min_occurrences" in options:
            self.min_occurrences = parse_min_int(
                self.code, "min_occurrences", options["min_occurrences"], 2
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag module constants sharing non-trivial literal values in one file."""
        groups = _collect_module_constants(node)
        for entries in groups.values():
            distinct_names = list(dict.fromkeys(name for _n, name, _lbl in entries))
            if len(distinct_names) < self.min_occurrences:
                continue
            first_node, _first_name, label = entries[0]
            joined = ", ".join(distinct_names)
            yield self.diagnostic(
                first_node,
                f"Literal {label} is assigned to {len(distinct_names)} >= "
                f"{self.min_occurrences} differently named module constants ({joined}) "
                "in this file (file-scope subset only; cross-module constants are deferred)",
            )


DRY_HEURISTIC_RULES: list[type[Rule]] = [
    RepeatedValidation,
    RepeatedConstantDefinition,
]

__all__ = [
    "DRY_HEURISTIC_RULES",
    "RepeatedConstantDefinition",
    "RepeatedValidation",
]

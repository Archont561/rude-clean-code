"""In-file DRY duplication detection Clean Code rule (CC501)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import definition_name, parse_nonneg_int

if TYPE_CHECKING:
    from rude.core.node import Node

_STUB_BODIES = frozenset({"pass", "..."})


def _is_docstring_stmt(stmt: Node | None) -> bool:
    if stmt is None or stmt.type != "expression_statement":
        return False
    children = stmt.named_children
    return len(children) == 1 and children[0].type == "string"


def _excluded_byte_ranges(body: Node) -> list[tuple[int, int]]:
    ranges = [(c.start_byte, c.end_byte) for c in body.find("comment")]
    first_stmt = next((c for c in body.named_children if c.type != "comment"), None)
    if first_stmt is not None and _is_docstring_stmt(first_stmt):
        ranges.append((first_stmt.start_byte, first_stmt.end_byte))
    return sorted(ranges)


def _strip_ranges(
    source: bytes, start: int, end: int, ranges: list[tuple[int, int]]
) -> str:
    chunks: list[bytes] = []
    cursor = start
    for r_start, r_end in ranges:
        if r_end <= cursor or r_start >= end:
            continue
        if r_start > cursor:
            chunks.append(source[cursor:r_start])
        cursor = max(cursor, min(end, r_end))
    if cursor < end:
        chunks.append(source[cursor:end])
    return b"".join(chunks).decode("utf-8", errors="replace")


def _normalized_body_lines(body: Node) -> list[str]:
    ranges = _excluded_byte_ranges(body)
    cleaned = _strip_ranges(body.ctx.source, body.start_byte, body.end_byte, ranges)
    return [line for raw in cleaned.splitlines() if (line := " ".join(raw.split()))]


class DuplicateFunctionBody(Rule):
    """CC501: Function duplicates another function body within the same file.

    Detects whitespace- and comment-normalised duplicate function bodies inside
    a single module (cross-file duplication is out of scope and deferred to CC502).
    """

    code: ClassVar[str] = "CC501"
    message: ClassVar[str] = "Function duplicates another function body in this file"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    min_lines: int = 5

    def __init__(self) -> None:
        self.min_lines = 5

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum normalized body line threshold via ``min_lines``."""
        if "min_lines" in options:
            self.min_lines = parse_nonneg_int(
                self.code, "min_lines", options["min_lines"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag functions in this file duplicating an earlier function body."""
        seen: dict[str, tuple[str, int]] = {}
        for fn in node.find("function_definition"):
            body = fn.body
            if body is None:
                continue
            lines = _normalized_body_lines(body)
            if len(lines) < self.min_lines:
                continue
            if len(lines) == 1 and lines[0] in _STUB_BODIES:
                continue
            signature = "\n".join(lines)
            name = definition_name(fn)
            if signature not in seen:
                seen[signature] = (name, fn.line)
                continue
            orig_name, orig_line = seen[signature]
            yield self.diagnostic(
                fn,
                f"Function '{name}' duplicates the body of '{orig_name}' "
                f"(line {orig_line}) within this file ({len(lines)} >= {self.min_lines} "
                "body lines); extract a shared helper (same-file check only; "
                "cross-file duplication is CC502)",
            )


DRY_RULES: list[type[Rule]] = [DuplicateFunctionBody]

__all__ = ["DRY_RULES", "DuplicateFunctionBody"]

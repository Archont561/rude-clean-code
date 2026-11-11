"""Docstring section, placeholder, and public-API target analysis helpers."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING

from rude_clean_code._scope import (
    definition_name,
    node_decorators,
    unwrap_decorated,
)

if TYPE_CHECKING:
    from rude.core.node import Node

_GOOGLE_PARAM_HEADERS = frozenset(
    {"args", "arguments", "keyword args", "keyword arguments"}
)
_SPHINX_PARAM_RE = re.compile(
    r"^\s*:param\s+(?:[^:\s]+\s+)?(\*{0,2}[A-Za-z_][A-Za-z0-9_]*)\s*:"
)
_GOOGLE_PARAM_ENTRY_RE = re.compile(
    r"^(\*{0,2}[A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*:"
)
_RETURNS_HEADER_RE = re.compile(r"^(?:returns?)\s*:\s*$", re.IGNORECASE)
_NUMPY_RETURNS_RE = re.compile(r"(?m)^\s*returns?\s*\n\s*-{3,}\s*$", re.IGNORECASE)
_SPHINX_RETURNS_RE = re.compile(r"(?m)^\s*:returns?:")
_PLACEHOLDER_PREFIX_RE = re.compile(r"^(?:TODO|FIXME)(?:[:(\s]|$)", re.IGNORECASE)


def is_placeholder_docstring(content: str) -> bool:
    """Return whether *content* is empty, punctuation-only, or a TODO/FIXME stub."""
    stripped = content.strip()
    if not stripped:
        return True
    if not any(ch.isalnum() for ch in stripped):
        return True
    first_line = stripped.splitlines()[0].strip()
    return _PLACEHOLDER_PREFIX_RE.match(first_line) is not None


def _is_setter_or_overload(func_node: Node) -> bool:
    for dec in node_decorators(func_node):
        if dec == "overload" or dec.endswith((".setter", ".deleter")):
            return True
    return False


def _has_module_statements(module_node: Node) -> bool:
    return any(child.type != "comment" for child in module_node.named_children)


def _walk_class_body(
    cls_node: Node,
    *,
    check_classes: bool,
) -> Iterator[tuple[str, Node]]:
    name = definition_name(cls_node)
    if name.startswith("_"):
        return
    if check_classes:
        yield ("class", cls_node)
    body = cls_node.body
    if body is None:
        return
    for item in body.named_children:
        target = unwrap_decorated(item)
        if target.type == "class_definition":
            yield from _walk_class_body(target, check_classes=check_classes)
        elif target.type == "function_definition":
            fn_name = definition_name(target)
            if not fn_name.startswith("_") and not _is_setter_or_overload(target):
                yield ("function", target)


def iter_public_api_definitions(
    module_node: Node,
    *,
    check_modules: bool,
    check_classes: bool,
) -> Iterator[tuple[str, Node]]:
    """Yield public ``(kind, node)`` pairs subject to docstring checks."""
    if check_modules and _has_module_statements(module_node):
        yield ("module", module_node)
    for child in module_node.named_children:
        target = unwrap_decorated(child)
        if target.type == "class_definition":
            yield from _walk_class_body(target, check_classes=check_classes)
        elif target.type == "function_definition":
            fn_name = definition_name(target)
            if not fn_name.startswith("_") and not _is_setter_or_overload(target):
                yield ("function", target)


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _collect_google_section_params(lines: list[str], start: int) -> list[str]:
    base_indent = _line_indent(lines[start])
    item_indent: int | None = None
    found: list[str] = []
    for raw in lines[start + 1 :]:
        stripped = raw.strip()
        if not stripped:
            continue
        indent = _line_indent(raw)
        if indent <= base_indent:
            break
        if item_indent is None or indent < item_indent:
            item_indent = indent
        if indent != item_indent:
            continue
        match = _GOOGLE_PARAM_ENTRY_RE.match(stripped)
        if match:
            found.append(match.group(1).lstrip("*"))
    return found


def _collect_numpy_section_params(lines: list[str], start: int) -> list[str]:
    base_indent = _line_indent(lines[start])
    found: list[str] = []
    for raw in lines[start + 2 :]:
        stripped = raw.strip()
        if not stripped:
            continue
        indent = _line_indent(raw)
        if indent > base_indent:
            continue
        if ":" not in stripped and stripped.endswith("-"):
            break
        header_part = stripped.split(":", 1)[0]
        for token in header_part.split(","):
            name = token.strip().lstrip("*")
            if name.isidentifier():
                found.append(name)
    return found


def extract_documented_params(docstring: str) -> tuple[bool, list[str]]:
    """Return ``(has_param_section, parameter_names)`` parsed from Google/NumPy/Sphinx docs."""
    lines = docstring.splitlines()
    has_section = False
    params: list[str] = []
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        lower = stripped.lower()
        if lower.endswith(":") and lower[:-1].strip() in _GOOGLE_PARAM_HEADERS:
            has_section = True
            params.extend(_collect_google_section_params(lines, idx))
        elif (
            lower == "parameters"
            and idx + 1 < len(lines)
            and re.match(r"^\s*-{3,}\s*$", lines[idx + 1])
        ):
            has_section = True
            params.extend(_collect_numpy_section_params(lines, idx))
        elif (sphinx_match := _SPHINX_PARAM_RE.match(raw)) is not None:
            has_section = True
            params.append(sphinx_match.group(1).lstrip("*"))
    deduped = list(dict.fromkeys(p for p in params if p))
    return has_section, deduped


def has_returns_section(docstring: str) -> bool:
    """Return whether *docstring* declares an explicit ``Returns:`` or ``:returns:`` section."""
    if _NUMPY_RETURNS_RE.search(docstring) or _SPHINX_RETURNS_RE.search(docstring):
        return True
    return any(
        _RETURNS_HEADER_RE.match(line.strip()) for line in docstring.splitlines()
    )

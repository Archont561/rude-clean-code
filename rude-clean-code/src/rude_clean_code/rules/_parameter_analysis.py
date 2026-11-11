"""Shared function parameter, body-stub, and visible-class analysis helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rude_clean_code._scope import definition_name, node_decorators, unwrap_decorated

if TYPE_CHECKING:
    from rude.core.node import Node

_BOOL_TYPE_NAMES = frozenset({"bool", "builtins.bool"})
_STUB_TEXTS = frozenset({"pass", "..."})


@dataclass(frozen=True, slots=True)
class ParamSpec:
    """Normalized function parameter metadata extracted from tree-sitter."""

    name: str
    type_node: Node | None
    default_node: Node | None
    node: Node
    is_variadic: bool


_SPLAT_TYPES = frozenset({"list_splat_pattern", "dictionary_splat_pattern"})


def _extract_param_identity(param: Node) -> tuple[str | None, bool]:
    if param.type == "identifier":
        return (param.text or None), False
    if param.type in _SPLAT_TYPES:
        ident = next(
            (c.text for c in param.named_children if c.type == "identifier" and c.text),
            None,
        )
        return ident, True
    target = param.child_by_field("name")
    if target is None:
        target = next(
            (
                c
                for c in param.named_children
                if c.type == "identifier" or c.type in _SPLAT_TYPES
            ),
            None,
        )
    if target is not None:
        return _extract_param_identity(target)
    return None, False


def has_var_keyword_param(func_node: Node) -> bool:
    """Return whether *func_node* declares a ``**kwargs`` parameter."""
    for param in func_node.parameters:
        if param.type == "dictionary_splat_pattern":
            return True
        if param.type == "typed_parameter" and any(
            child.type == "dictionary_splat_pattern" for child in param.named_children
        ):
            return True
    return False


def parse_parameters(func_node: Node) -> list[ParamSpec]:
    """Return normalized parameter specs in declaration order."""
    specs: list[ParamSpec] = []
    for param in func_node.parameters:
        name, is_variadic = _extract_param_identity(param)
        if not name:
            continue
        specs.append(
            ParamSpec(
                name=name,
                type_node=param.child_by_field("type"),
                default_node=param.child_by_field("value"),
                node=param,
                is_variadic=is_variadic,
            )
        )
    return specs


def is_bool_annotation(type_node: Node | None) -> bool:
    """Return whether *type_node* represents a simple or optional ``bool`` type."""
    if type_node is None:
        return False
    compact = type_node.text.replace(" ", "")
    if compact in _BOOL_TYPE_NAMES:
        return True
    if compact.startswith(("Optional[", "typing.Optional[")) and compact.endswith("]"):
        inner = compact.split("[", 1)[1][:-1]
        return inner in _BOOL_TYPE_NAMES
    if "|" in compact:
        parts = {part for part in compact.split("|") if part}
        return bool(parts & _BOOL_TYPE_NAMES) and parts <= (_BOOL_TYPE_NAMES | {"None"})
    return False


def is_bool_default(default_node: Node | None) -> bool:
    """Return whether *default_node* is literally ``True`` or ``False``."""
    return default_node is not None and default_node.type in {"true", "false"}


def body_statements(block: Node) -> list[Node]:
    """Return non-comment, non-docstring statements inside a block node."""
    stmts = [child for child in block.named_children if child.type != "comment"]
    if not stmts:
        return stmts
    first = stmts[0]
    if (
        first.type == "expression_statement"
        and len(first.named_children) == 1
        and first.named_children[0].type == "string"
    ):
        return stmts[1:]
    return stmts


def is_raise_not_implemented(stmt: Node) -> bool:
    """Return whether *stmt* directly raises ``NotImplementedError``."""
    if stmt.type != "raise_statement":
        return False
    children = stmt.named_children
    if not children:
        return False
    target = children[0]
    if target.type == "call":
        callee = target.child_by_field("function")
        return callee is not None and callee.text in {
            "NotImplementedError",
            "builtins.NotImplementedError",
        }
    return target.text in {"NotImplementedError", "builtins.NotImplementedError"}


def is_stub_body(func_node: Node) -> bool:
    """Return whether *func_node* only contains ``pass``, ``...``, or ``NotImplementedError``."""
    body = func_node.body
    if body is None:
        return True
    stmts = body_statements(body)
    if not stmts:
        return True
    if len(stmts) != 1:
        return False
    stmt = stmts[0]
    if stmt.text.strip() in _STUB_TEXTS:
        return True
    return is_raise_not_implemented(stmt)


def only_raises_not_implemented(func_node: Node) -> bool:
    """Return whether *func_node*'s non-docstring body consists solely of raising ``NotImplementedError``."""
    body = func_node.body
    if body is None:
        return False
    stmts = body_statements(body)
    return len(stmts) == 1 and is_raise_not_implemented(stmts[0])


def direct_class_methods(class_node: Node) -> list[tuple[Node, list[str]]]:
    """Return ``(method_node, decorators)`` pairs defined directly on *class_node*."""
    body = class_node.body
    if body is None:
        return []
    result: list[tuple[Node, list[str]]] = []
    for child in body.named_children:
        target = unwrap_decorated(child)
        if target.type != "function_definition":
            continue
        result.append((target, node_decorators(target)))
    return result


def collect_module_classes(module_node: Node) -> dict[str, Node]:
    """Return a name-to-node index for non-duplicated classes visible in *module_node*."""
    classes: dict[str, Node] = {}
    for cls_node in module_node.find("class_definition"):
        name = definition_name(cls_node)
        classes.setdefault(name, cls_node)
    return classes

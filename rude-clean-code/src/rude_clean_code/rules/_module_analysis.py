"""AST and scope-clustering helpers for module organization rules."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from rude.providers import NO_SCOPE
from rude.utils import extract_string_content, iter_import_aliases

from rude_clean_code._scope import definition_name, is_dunder, unwrap_decorated

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.providers.semantic import SemanticModel

ALL_NAME = "__all__"
INIT_FILENAME = "__init__.py"
_EXPR_STMT = "expression_statement"
_ASSIGNMENT_TYPES = frozenset({"assignment", "augmented_assignment"})
_DEF_KINDS = frozenset({"function_definition", "class_definition"})
_FACADE_ONLY_IMPORTS = frozenset({"typing.TYPE_CHECKING"})
_PASSTHROUGH_STATEMENTS = frozenset(
    {
        "comment",
        "import_statement",
        "import_from_statement",
        "future_import_statement",
    }
)


def has_enclosing_scope_def(node: Node) -> bool:
    """Return whether *node* sits inside any function or class definition."""
    parent = node.parent
    while parent is not None:
        if parent.type in _DEF_KINDS:
            return True
        parent = parent.parent
    return False


def is_type_checking_if(stmt: Node) -> bool:
    """Return whether *stmt* is a pure ``if [typing.]TYPE_CHECKING:`` guard."""
    if stmt.type != "if_statement":
        return False
    condition = stmt.child_by_field("condition")
    if condition is None or condition.text not in {
        "TYPE_CHECKING",
        "typing.TYPE_CHECKING",
    }:
        return False
    return not any(
        child.type in {"elif_clause", "else_clause"} for child in stmt.named_children
    )


def _is_module_docstring(stmt: Node, is_first_non_comment: bool) -> bool:
    if not is_first_non_comment or stmt.type != _EXPR_STMT:
        return False
    children = stmt.named_children
    return len(children) == 1 and children[0].type == "string"


def _assignment_targets(node: Node) -> list[str] | None:
    targets: list[str] = []
    current: Node | None = node
    while current is not None and current.type in _ASSIGNMENT_TYPES:
        left = current.child_by_field("left")
        if left is None or left.type != "identifier":
            return None
        targets.append(left.text)
        current = current.child_by_field("right")
    return targets


def _all_assignment_node(stmt: Node) -> Node | None:
    if stmt.type != _EXPR_STMT or len(stmt.named_children) != 1:
        return None
    inner = stmt.named_children[0]
    if inner.type not in _ASSIGNMENT_TYPES:
        return None
    left = inner.child_by_field("left")
    if left is None or left.type != "identifier" or left.text != ALL_NAME:
        return None
    return inner


def extract_string_nodes(node: Node) -> Iterator[tuple[Node, str]]:
    """Yield every string literal descendant node paired with its unquoted content."""
    for child in node.walk():
        if child.type == "string":
            content = extract_string_content(child.text)
            if content is not None:
                yield child, content


def _bound_import_name(full_name: str, alias: str | None, *, is_from: bool) -> str:
    if alias is not None:
        return alias
    if is_from:
        return full_name.rsplit(".", maxsplit=1)[-1]
    return full_name.split(".", maxsplit=1)[0]


def collect_top_level_defs(module_node: Node) -> list[tuple[Node, Node, str]]:
    """Return ``(outer_node, inner_def, name)`` tuples for top-level definitions."""
    defs: list[tuple[Node, Node, str]] = []
    for child in module_node.named_children:
        target = unwrap_decorated(child)
        if target.type in _DEF_KINDS:
            defs.append((child, target, definition_name(target)))
    return defs


def _uses_within_span(
    outer: Node,
    model: SemanticModel,
    module_uses: tuple[Any, ...],
) -> set[str]:
    used = {
        use.name
        for scope in model.scopes
        if outer.start_byte <= scope.start_byte <= outer.end_byte
        for use in scope.uses
    }
    used.update(
        use.name
        for use in module_uses
        if outer.start_byte <= use.start_byte <= outer.end_byte
    )
    return used


def build_symbol_clusters(
    defs: list[tuple[Node, Node, str]],
    model: SemanticModel,
) -> list[list[str]]:
    """Group interconnected top-level definitions into connected clusters."""
    if len(defs) < 2:
        return []
    names = [name for _, _, name in defs]
    name_set = set(names)
    adj: dict[str, set[str]] = {name: set() for name in names}
    module_uses = (
        tuple(model.scopes[model.module_scope].uses)
        if model.module_scope != NO_SCOPE
        and 0 <= model.module_scope < len(model.scopes)
        else ()
    )
    for outer, _, name in defs:
        for target in _uses_within_span(outer, model, module_uses) & name_set:
            if target != name:
                adj[name].add(target)
                adj[target].add(name)
    return _connected_components(names, adj)


def _connected_components(
    names: list[str],
    adj: dict[str, set[str]],
) -> list[list[str]]:
    visited: set[str] = set()
    clusters: list[list[str]] = []
    for start in names:
        if start in visited:
            continue
        cluster: list[str] = []
        queue: deque[str] = deque([start])
        visited.add(start)
        while queue:
            current = queue.popleft()
            cluster.append(current)
            for neighbor in sorted(adj[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        clusters.append(cluster)
    return clusters


def format_clusters(clusters: list[list[str]]) -> str:
    """Format up to three detected symbol clusters for a split suggestion."""
    formatted = ["/".join(cluster[:2]) for cluster in clusters[:3]]
    if len(clusters) > 3:
        formatted.append("...")
    return ", ".join(formatted)


def describe_non_facade_statement(stmt: Node) -> tuple[str, str]:
    """Return ``(kind, label)`` describing a disallowed ``__init__.py`` statement."""
    target = unwrap_decorated(stmt)
    if target.type in _DEF_KINDS:
        kind = "class" if target.type == "class_definition" else "function"
        return kind, definition_name(target)
    if stmt.type == _EXPR_STMT and stmt.named_children:
        inner = stmt.named_children[0]
        if inner.type in _ASSIGNMENT_TYPES:
            targets = _assignment_targets(inner)
            if targets:
                return "assignment", ", ".join(targets)
    return "statement", stmt.type


def _is_allowed_init_assignment(
    inner: Node,
    allowed_names: frozenset[str],
) -> bool:
    targets = _assignment_targets(inner)
    if targets is None:
        return False
    return all(
        name == ALL_NAME or is_dunder(name) or name in allowed_names for name in targets
    )


def is_allowed_init_statement(
    stmt: Node,
    is_first_non_comment: bool,
    allowed_names: frozenset[str],
    *,
    allow_lazy_getattr: bool,
) -> bool:
    """Return whether *stmt* is permitted inside a facade ``__init__.py``."""
    allowed = (
        stmt.type in _PASSTHROUGH_STATEMENTS
        or _is_module_docstring(stmt, is_first_non_comment)
        or is_type_checking_if(stmt)
    )
    if not allowed and stmt.type == "function_definition":
        allowed = allow_lazy_getattr and stmt.name in {"__getattr__", "__dir__"}
    elif not allowed and stmt.type == _EXPR_STMT and len(stmt.named_children) == 1:
        inner = stmt.named_children[0]
        if inner.type in _ASSIGNMENT_TYPES:
            allowed = _is_allowed_init_assignment(inner, allowed_names)
    return allowed


def _collect_import_reexports(stmt: Node) -> list[str]:
    reexports: list[str] = []
    for item in iter_import_aliases(stmt):
        if item.full_name in _FACADE_ONLY_IMPORTS and item.alias is None:
            continue
        bound = _bound_import_name(item.full_name, item.alias, is_from=item.is_from)
        if bound and not bound.startswith("_"):
            reexports.append(bound)
    return reexports


def _is_type_checking_import_only(stmt: Node) -> bool:
    if stmt.type != "import_from_statement":
        return False
    aliases = list(iter_import_aliases(stmt))
    return bool(aliases) and all(
        item.full_name in _FACADE_ONLY_IMPORTS and item.alias is None
        for item in aliases
    )


def collect_init_exports(
    module_node: Node,
) -> tuple[bool, list[str] | None, list[str]]:
    """Inspect an ``__init__.py`` module for runtime statements, ``__all__``, and imports."""
    has_runtime_content = False
    all_exports: list[str] | None = None
    public_reexports: list[str] = []
    seen_first = False
    for stmt in module_node.named_children:
        if stmt.type == "comment":
            continue
        is_first = not seen_first
        seen_first = True
        if _is_module_docstring(stmt, is_first) or _is_skippable_init_stmt(stmt):
            continue
        has_runtime_content = True
        assign = _all_assignment_node(stmt)
        if assign is not None:
            right = assign.child_by_field("right")
            all_exports = [] if all_exports is None else all_exports
            if right is not None:
                all_exports.extend(val for _, val in extract_string_nodes(right))
        elif stmt.type in {"import_statement", "import_from_statement"}:
            public_reexports.extend(_collect_import_reexports(stmt))
    return has_runtime_content, all_exports, public_reexports


def _is_skippable_init_stmt(stmt: Node) -> bool:
    return (
        stmt.type == "future_import_statement"
        or is_type_checking_if(stmt)
        or _is_type_checking_import_only(stmt)
    )

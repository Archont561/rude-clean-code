"""Class cohesion, constructor coupling, and interface surface rules (CC204-CC206)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    ThresholdRule,
    definition_name,
    is_dunder,
    iter_own_scope,
    parse_min_int,
    parse_nonneg_int,
)
from rude_clean_code.rules._parameter_analysis import (
    ParamSpec,
    direct_class_methods,
    parse_parameters,
)

if TYPE_CHECKING:
    from rude.core.node import Node

_NON_INSTANCE_DECORATORS = frozenset({"staticmethod", "classmethod", "overload"})
_SKIP_COHESION_METHODS = frozenset({"__init__", "__new__", "__post_init__"})


def _self_member_accesses(func_node: Node) -> set[str]:
    body = func_node.body
    if body is None:
        return set()
    members: set[str] = set()
    for current in iter_own_scope(body):
        if current.type != "attribute":
            continue
        receiver = current.child_by_field("object")
        attr = current.child_by_field("attribute")
        is_self = (
            receiver is not None
            and receiver.type == "identifier"
            and receiver.text == "self"
        )
        if is_self and attr is not None and attr.text:
            members.add(attr.text)
    return members


def _count_connected_clusters(
    method_members: dict[str, set[str]],
    method_names: set[str],
) -> int:
    adjacency: dict[str, set[str]] = defaultdict(set)
    by_member: dict[str, list[str]] = defaultdict(list)
    for method, members in method_members.items():
        for member in members:
            by_member[member].append(method)
            if member in method_names and member != method:
                adjacency[method].add(member)
                adjacency[member].add(method)
    for peers in by_member.values():
        anchor = peers[0]
        for other in peers[1:]:
            adjacency[anchor].add(other)
            adjacency[other].add(anchor)
    return _count_components(list(method_members), adjacency)


def _count_components(nodes: list[str], adjacency: dict[str, set[str]]) -> int:
    visited: set[str] = set()
    clusters = 0
    for start in nodes:
        if start in visited:
            continue
        clusters += 1
        stack = [start]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(adjacency[current] - visited)
    return clusters


def _is_dependency_param(spec: ParamSpec) -> bool:
    return (
        not spec.is_variadic
        and spec.name not in {"self", "cls"}
        and spec.type_node is not None
    )


class ExcessiveConstructorDependencies(ThresholdRule):
    """CC204: Constructor declares too many annotated dependencies."""

    code: ClassVar[str] = "CC204"
    message: ClassVar[str] = "Constructor declares too many annotated dependencies"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CLASS_DEFINITION}
    option_name: ClassVar[str] = "max_dependencies"
    default_limit: ClassVar[int] = 5

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag ``__init__`` methods declaring more annotated parameters than allowed."""
        cls_name = definition_name(node)
        for method, _decs in direct_class_methods(node):
            if definition_name(method) != "__init__":
                continue
            deps = [
                spec for spec in parse_parameters(method) if _is_dependency_param(spec)
            ]
            msg = (
                f"Constructor '{cls_name}.__init__' requests {len(deps)} > {self.limit} "
                "annotated dependencies; may indicate high coupling — consider "
                "splitting responsibilities or grouping collaborators"
            )
            yield from self.emit_if_exceeds(method, len(deps), msg)


class MultipleResponsibilities(Rule):
    """CC205: Class methods form disjoint attribute-access clusters."""

    code: ClassVar[str] = "CC205"
    message: ClassVar[str] = (
        "Disjoint method clusters suggest multiple responsibilities"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CLASS_DEFINITION}

    max_clusters: int = 2
    min_methods: int = 5

    def __init__(self) -> None:
        self.max_clusters = 2
        self.min_methods = 5

    def configure(self, options: dict[str, Any]) -> None:
        """Configure cluster count ceiling and minimum method count."""
        if "max_clusters" in options:
            self.max_clusters = parse_min_int(
                self.code, "max_clusters", options["max_clusters"], 1
            )
        if "min_methods" in options:
            self.min_methods = parse_min_int(
                self.code, "min_methods", options["min_methods"], 1
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Report disconnected ``self.<attr>`` method clusters on large enough classes."""
        method_members: dict[str, set[str]] = {}
        for method, decs in direct_class_methods(node):
            name = definition_name(method)
            if name in _SKIP_COHESION_METHODS or any(
                d in _NON_INSTANCE_DECORATORS for d in decs
            ):
                continue
            members = _self_member_accesses(method)
            if members:
                method_members.setdefault(name, set()).update(members)
        if len(method_members) < self.min_methods:
            return
        clusters = _count_connected_clusters(method_members, set(method_members))
        if clusters > self.max_clusters:
            cls_name = definition_name(node)
            yield self.diagnostic(
                node,
                f"Class '{cls_name}' has {clusters} > {self.max_clusters} disconnected "
                "method/attribute clusters, suggesting multiple responsibilities; "
                "consider extracting cohesive helper classes",
            )


class OversizedInterfaceSurface(Rule):
    """CC206: Class exposes a wide public method surface (per-file ISP indicator)."""

    code: ClassVar[str] = "CC206"
    message: ClassVar[str] = "Class exposes an oversized public interface surface"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.CLASS_DEFINITION}

    max_public_methods: int = 10

    def __init__(self) -> None:
        self.max_public_methods = 10

    def configure(self, options: dict[str, Any]) -> None:
        """Configure maximum public method allowance via ``max_public_methods``."""
        if "max_public_methods" in options:
            self.max_public_methods = parse_nonneg_int(
                self.code, "max_public_methods", options["max_public_methods"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag classes with more distinct public methods than ``max_public_methods``."""
        public_names: set[str] = set()
        for method, decs in direct_class_methods(node):
            name = definition_name(method)
            if name.startswith("_") or is_dunder(name) or "overload" in decs:
                continue
            public_names.add(name)
        count = len(public_names)
        if count > self.max_public_methods:
            cls_name = definition_name(node)
            yield self.diagnostic(
                node,
                f"Class '{cls_name}' exposes {count} > {self.max_public_methods} public "
                "methods, suggesting an oversized interface; caller usage is outside "
                "per-file scope — consider splitting focused protocols",
            )


CLASS_HEURISTIC_RULES: list[type[Rule]] = [
    ExcessiveConstructorDependencies,
    MultipleResponsibilities,
    OversizedInterfaceSurface,
]

__all__ = [
    "CLASS_HEURISTIC_RULES",
    "ExcessiveConstructorDependencies",
    "MultipleResponsibilities",
    "OversizedInterfaceSurface",
]

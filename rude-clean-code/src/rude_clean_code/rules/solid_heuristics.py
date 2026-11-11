"""In-file inheritance LSP and ISP indicator rules (CC602-CC603)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    base_candidate_names,
    definition_name,
    iter_own_scope,
    parse_nonneg_int,
)
from rude_clean_code.rules._parameter_analysis import (
    ParamSpec,
    collect_module_classes,
    direct_class_methods,
    is_stub_body,
    only_raises_not_implemented,
    parse_parameters,
)

if TYPE_CHECKING:
    from rude.core.node import Node

_EXEMPT_OVERRIDE_METHODS = frozenset(
    {"__init__", "__new__", "__post_init__", "__init_subclass__"}
)


def _visible_in_file_ancestors(
    cls_node: Node,
    classes: dict[str, Node],
) -> list[tuple[str, Node]]:
    seen: set[str] = {definition_name(cls_node)}
    ancestors: list[tuple[str, Node]] = []
    queue: list[Node] = [cls_node]
    while queue:
        current = queue.pop(0)
        for base in current.bases:
            if base.type == "keyword_argument":
                continue
            for candidate in base_candidate_names(base):
                if candidate in classes and candidate not in seen:
                    seen.add(candidate)
                    base_node = classes[candidate]
                    ancestors.append((candidate, base_node))
                    queue.append(base_node)
                    break
    return ancestors


def _method_map(cls_node: Node) -> dict[str, tuple[Node, list[str]]]:
    methods: dict[str, tuple[Node, list[str]]] = {}
    for method, decs in direct_class_methods(cls_node):
        if "overload" in decs:
            continue
        methods[definition_name(method)] = (method, decs)
    return methods


def _is_abstract_or_stub(method_node: Node, decs: list[str]) -> bool:
    return "abstractmethod" in decs or is_stub_body(method_node)


def _narrowed_default_params(
    base_method: Node,
    sub_method: Node,
) -> list[str]:
    sub_specs = parse_parameters(sub_method)
    if any(spec.is_variadic for spec in sub_specs):
        return []
    sub_by_name: dict[str, ParamSpec] = {spec.name: spec for spec in sub_specs}
    narrowed: list[str] = []
    for base_spec in parse_parameters(base_method):
        if base_spec.is_variadic or base_spec.name in {"self", "cls"}:
            continue
        if base_spec.default_node is None:
            continue
        sub_spec = sub_by_name.get(base_spec.name)
        if sub_spec is not None and sub_spec.default_node is None:
            narrowed.append(base_spec.name)
    return narrowed


def _return_shape(method_node: Node) -> str:
    body = method_node.body
    if body is None:
        return "empty"
    has_value = False
    has_none = False
    has_raise = False
    for current in iter_own_scope(body):
        if current.type == "raise_statement":
            has_raise = True
        elif current.type == "return_statement":
            children = current.named_children
            if not children or children[0].type == "none":
                has_none = True
            else:
                has_value = True
    if has_value:
        return "value"
    if has_raise and not has_none:
        return "raises"
    return "none"


def _discards_return_shape(
    base_method: Node,
    base_decs: list[str],
    sub_method: Node,
    sub_decs: list[str],
) -> bool:
    if _is_abstract_or_stub(base_method, base_decs) or _is_abstract_or_stub(
        sub_method, sub_decs
    ):
        return False
    ret_ann = base_method.child_by_field("return_type")
    if ret_ann is not None and ret_ann.text.strip() == "None":
        return False
    return _return_shape(base_method) == "value" and _return_shape(sub_method) == "none"


def _method_lsp_messages(
    sub_name: str,
    base_name: str,
    method_name: str,
    base_pair: tuple[Node, list[str]],
    sub_pair: tuple[Node, list[str]],
) -> list[str]:
    base_method, base_decs = base_pair
    sub_method, sub_decs = sub_pair
    reasons: list[str] = []
    if not _is_abstract_or_stub(base_method, base_decs) and only_raises_not_implemented(
        sub_method
    ):
        reasons.append(
            f"Method '{sub_name}.{method_name}' raises NotImplementedError when visible base "
            f"'{base_name}.{method_name}' is concrete; suggests a potential Liskov Substitution mismatch — consider splitting interfaces"
        )
    if narrowed := _narrowed_default_params(base_method, sub_method):
        reasons.append(
            f"Method '{sub_name}.{method_name}' removes default value(s) for '{', '.join(narrowed)}' "
            f"provided by visible base '{base_name}'; suggests a potential Liskov Substitution mismatch — keep base defaults or split contracts"
        )
    if _discards_return_shape(base_method, base_decs, sub_method, sub_decs):
        reasons.append(
            f"Method '{sub_name}.{method_name}' returns None where visible base "
            f"'{base_name}.{method_name}' returns a value; suggests a potential Liskov Substitution mismatch"
        )
    return reasons


class SuspiciousOverriddenMethod(Rule):
    """CC602: Subclass override potentially narrows or breaks a visible base contract."""

    code: ClassVar[str] = "CC602"
    message: ClassVar[str] = (
        "Override may break substitutability with visible base class"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag suspicious overrides only when an in-file base method is visible."""
        classes = collect_module_classes(node)
        for cls_name, cls_node in classes.items():
            ancestors = _visible_in_file_ancestors(cls_node, classes)
            if ancestors:
                yield from self._check_class_overrides(cls_name, cls_node, ancestors)

    def _collect_ancestor_methods(
        self, ancestors: list[tuple[str, Node]]
    ) -> dict[str, tuple[str, Node, list[str]]]:
        ancestor_methods: dict[str, tuple[str, Node, list[str]]] = {}
        for base_name, base_node in ancestors:
            for m_name, (m_node, m_decs) in _method_map(base_node).items():
                ancestor_methods.setdefault(m_name, (base_name, m_node, m_decs))
        return ancestor_methods

    def _check_class_overrides(
        self,
        cls_name: str,
        cls_node: Node,
        ancestors: list[tuple[str, Node]],
    ) -> Iterator[Diagnostic]:
        ancestor_methods = self._collect_ancestor_methods(ancestors)
        for m_name, (sub_method, sub_decs) in _method_map(cls_node).items():
            if m_name in _EXEMPT_OVERRIDE_METHODS or "abstractmethod" in sub_decs:
                continue
            if m_name not in ancestor_methods:
                continue
            base_name, base_method, base_decs = ancestor_methods[m_name]
            for msg in _method_lsp_messages(
                cls_name,
                base_name,
                m_name,
                (base_method, base_decs),
                (sub_method, sub_decs),
            ):
                yield self.diagnostic(sub_method, msg)


def _unimplemented_inherited_methods(
    cls_node: Node,
    ancestors: list[tuple[str, Node]],
) -> list[str]:
    inherited = {
        m_name
        for _base_name, base_node in reversed(ancestors)
        for m_name in _method_map(base_node)
    }
    return [
        m_name
        for m_name, (sub_method, _decs) in _method_map(cls_node).items()
        if m_name in inherited and only_raises_not_implemented(sub_method)
    ]


class InterfaceSegregationIndicator(Rule):
    """CC603: Class leaves multiple methods of a visible base/interface unimplemented."""

    code: ClassVar[str] = "CC603"
    message: ClassVar[str] = (
        "Multiple unimplemented inherited methods suggest an overly broad interface"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    max_unimplemented: int = 2

    def __init__(self) -> None:
        self.max_unimplemented = 2

    def configure(self, options: dict[str, Any]) -> None:
        """Configure threshold of ``NotImplementedError`` overrides via ``max_unimplemented``."""
        if "max_unimplemented" in options:
            self.max_unimplemented = parse_nonneg_int(
                self.code, "max_unimplemented", options["max_unimplemented"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Suggest splitting visible base interfaces when many methods raise NotImplementedError."""
        classes = collect_module_classes(node)
        for cls_name, cls_node in classes.items():
            ancestors = _visible_in_file_ancestors(cls_node, classes)
            if not ancestors:
                continue
            unimplemented = _unimplemented_inherited_methods(cls_node, ancestors)
            if len(unimplemented) > self.max_unimplemented:
                base_label = ancestors[0][0]
                yield self.diagnostic(
                    cls_node,
                    f"Class '{cls_name}' leaves {len(unimplemented)} > "
                    f"{self.max_unimplemented} inherited methods raising NotImplementedError; "
                    f"suggests visible base/interface '{base_label}' may be too broad "
                    "— consider splitting smaller focused interfaces",
                )


SOLID_HEURISTIC_RULES: list[type[Rule]] = [
    SuspiciousOverriddenMethod,
    InterfaceSegregationIndicator,
]

__all__ = [
    "SOLID_HEURISTIC_RULES",
    "InterfaceSegregationIndicator",
    "SuspiciousOverriddenMethod",
]

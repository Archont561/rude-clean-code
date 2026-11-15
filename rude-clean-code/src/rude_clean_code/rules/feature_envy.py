"""Feature Envy indicator for external same-type pairs (CC606)."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    is_test_context,
    iter_own_scope,
    node_decorators,
    parse_bool_option,
    parse_min_int,
    parse_str_list_option,
)
from rude_clean_code.rules._parameter_analysis import parse_parameters

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

_COMPARISON_METHODS = frozenset({"__eq__", "__ne__", "__hash__"})

_GENERIC_ARGUMENT = re.compile(r"\[[^\[\]]*\]")

# Value and container annotations never flag: comparing two of them is ordinary
# data handling, not envy toward a type that owns behaviour.
_NON_TYPE_ANNOTATIONS = frozenset(
    {
        "Any",
        "Callable",
        "Iterable",
        "Iterator",
        "Mapping",
        "MutableMapping",
        "MutableSequence",
        "None",
        "NoneType",
        "Optional",
        "Path",
        "PurePath",
        "Sequence",
        "Union",
        "bool",
        "bytearray",
        "bytes",
        "complex",
        "dict",
        "float",
        "frozenset",
        "int",
        "list",
        "memoryview",
        "object",
        "set",
        "str",
        "tuple",
        "type",
    }
)


def _normalize_annotation(text: str) -> str:
    """Strip quotes, whitespace, and generic arguments from an annotation text."""
    cleaned = text.strip().strip("\"'").strip()
    while True:
        stripped = _GENERIC_ARGUMENT.sub("", cleaned)
        if stripped == cleaned:
            return cleaned.strip()
        cleaned = stripped


def _annotation_target(type_node: Node) -> str | None:
    """Return the bare type name of a same-type annotation candidate, if any."""
    if type_node.type != "type":
        return None
    target = _normalize_annotation(type_node.text)
    if not target or target.startswith("("):
        return None
    name = target.rsplit(".", maxsplit=1)[-1]
    if name in _NON_TYPE_ANNOTATIONS:
        return None
    if not name[:1].isalpha() and name[:1] != "_":
        return None
    return name


def _same_type_pairs(func_node: Node) -> dict[str, list[str]]:
    """Map each repeated non-builtin annotation to the parameters carrying it."""
    by_type: dict[str, list[str]] = {}
    for spec in parse_parameters(func_node):
        if spec.is_variadic or spec.name in {"self", "cls"}:
            continue
        if spec.type_node is None:
            continue
        target = _annotation_target(spec.type_node)
        if target is None:
            continue
        by_type.setdefault(target, []).append(spec.name)
    return {name: params for name, params in by_type.items() if len(params) >= 2}


def _receiving_parameter(attribute_node: Node, names: set[str]) -> str | None:
    """Return the parameter a chain's outermost receiver starts from."""
    current: Node | None = attribute_node
    while current is not None:
        if current.type == "attribute":
            current = current.child_by_field("object")
        elif current.type == "call":
            current = current.child_by_field("function")
        elif current.type == "parenthesized_expression" and current.named_children:
            current = current.named_children[0]
        elif current.type == "identifier":
            return current.text if current.text in names else None
        else:
            return None
    return None


def _enclosing_class_name(func_node: Node) -> str | None:
    parent = func_node.parent
    if parent is not None and parent.type == "decorated_definition":
        parent = parent.parent
    if parent is not None and parent.type == "block":
        owner = parent.parent
        if owner is not None and owner.type == "class_definition":
            return owner.name
    return None


class ExternalSameTypePairEnvy(Rule):
    """CC606: Helper compares two instances of a type defined elsewhere."""

    code: ClassVar[str] = "CC606"
    message: ClassVar[str] = "Helper reads two same-type parameters it does not own"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}

    min_attribute_reads: int = 2
    ignored_types: tuple[str, ...] = ()
    exclude_tests: bool = True

    def __init__(self) -> None:
        self.min_attribute_reads = 2
        self.ignored_types = ()
        self.exclude_tests = True

    def should_check_file(self, context: FileContext) -> bool:
        """Skip test modules unless ``exclude_tests`` is disabled."""
        return not (self.exclude_tests and is_test_context(context))

    def configure(self, options: dict[str, Any]) -> None:
        """Configure the attribute-read budget, ignored types, and test exclusion."""
        if "min_attribute_reads" in options:
            self.min_attribute_reads = parse_min_int(
                self.code, "min_attribute_reads", options["min_attribute_reads"], 2
            )
        if "ignored_types" in options:
            self.ignored_types = parse_str_list_option(
                self.code, "ignored_types", options["ignored_types"]
            )
        if "exclude_tests" in options:
            self.exclude_tests = parse_bool_option(
                self.code, "exclude_tests", options["exclude_tests"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag external helpers reading attributes across a same-type pair."""
        if node.name in _COMPARISON_METHODS or "dataclass" in node_decorators(node):
            return
        pairs = _same_type_pairs(node)
        if not pairs:
            return
        enclosing = _enclosing_class_name(node)
        body = node.body
        if body is None:
            return
        for type_name, param_names in pairs.items():
            if type_name in self.ignored_types or type_name == enclosing:
                continue
            reads = self._count_parameter_reads(body, set(param_names))
            if reads < self.min_attribute_reads:
                continue
            joined = ", ".join(f"'{name}'" for name in param_names)
            yield self.diagnostic(
                node,
                f"Helper compares {len(param_names)} '{type_name}' parameters "
                f"({joined}) through {reads} attribute reads; suggests Feature Envy — "
                f"consider moving this comparison onto '{type_name}' (an __eq__ method, "
                "a dataclass key field, or a method on the class)",
            )

    def _count_parameter_reads(self, body: Node, names: set[str]) -> int:
        reads = 0
        for current in iter_own_scope(body):
            if current.type != "attribute":
                continue
            if _receiving_parameter(current, names) is not None:
                reads += 1
        return reads


FEATURE_ENVY_RULES: list[type[Rule]] = [ExternalSameTypePairEnvy]

__all__ = ["FEATURE_ENVY_RULES", "ExternalSameTypePairEnvy"]

"""Shared call-target, enclosing-scope, method, and decorator matching helpers."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.rule import Rule

from rude_clean_code._scope import (
    definition_name,
    matches_path_patterns,
    parse_str_list_option,
    unwrap_decorated,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext


def file_matches_scope(
    context: FileContext,
    *,
    only_paths: tuple[str, ...] = (),
    exclude_paths: tuple[str, ...] = (),
) -> bool:
    """Return whether *context* is included by *only_paths* and not *exclude_paths*."""
    if exclude_paths and matches_path_patterns(context, exclude_paths):
        return False
    return not (only_paths and not matches_path_patterns(context, only_paths))


def apply_str_list_options(
    rule: Rule,
    options: dict[str, Any],
    *option_names: str,
) -> None:
    """Validate and assign tuple-of-strings attributes present in *options*."""
    for name in option_names:
        if name in options:
            setattr(rule, name, parse_str_list_option(rule.code, name, options[name]))


def _is_self_like_receiver(receiver: Node | None) -> bool:
    if receiver is None:
        return False
    if receiver.type == "identifier":
        return receiver.text in {"self", "cls"}
    if receiver.type == "call":
        callee = receiver.child_by_field("function")
        return callee is not None and callee.text == "super"
    return False


def _attribute_target_candidates(func: Node) -> tuple[str, str] | None:
    if _is_self_like_receiver(func.child_by_field("object")):
        return None
    attr = func.child_by_field("attribute")
    if attr is None or not func.text or not attr.text:
        return None
    return (func.text, attr.text)


def call_target_candidates(call_node: Node) -> tuple[str, str] | None:
    """Return ``(full_name, short_name)`` for a direct or subscripted call node."""
    func = call_node.child_by_field("function")
    while func is not None and func.type == "subscript":
        func = func.child_by_field("value")
    result: tuple[str, str] | None = None
    if func is not None:
        if func.type == "identifier" and func.text:
            result = (func.text, func.text)
        elif func.type == "attribute":
            result = _attribute_target_candidates(func)
    return result


def match_configured_symbol(
    full_name: str,
    short_name: str,
    configured: tuple[str, ...],
) -> str | None:
    """Return the first configured symbol matching *full_name* or *short_name*."""
    for target in configured:
        if "." in target:
            if full_name == target or full_name.endswith(f".{target}"):
                return target
        elif short_name == target:
            return target
    return None


def enclosing_function_names(node: Node) -> Iterator[str]:
    """Yield names of enclosing ``function_definition`` ancestors from inner to outer."""
    current = node.parent
    while current is not None:
        if current.type == "function_definition":
            yield definition_name(current)
        current = current.parent


def enclosing_class_name(node: Node) -> str | None:
    """Return the innermost enclosing ``class_definition`` name, if any."""
    current = node.parent
    while current is not None:
        if current.type == "class_definition":
            return definition_name(current)
        current = current.parent
    return None


def direct_method_names(class_node: Node) -> frozenset[str]:
    """Return direct method names defined in *class_node*'s body."""
    body = class_node.body
    if body is None:
        return frozenset()
    names: set[str] = set()
    for child in body.named_children:
        target = unwrap_decorated(child)
        if target.type == "function_definition":
            names.add(definition_name(target))
    return frozenset(names)


def matches_decorator(
    attached: Sequence[str],
    required: tuple[str, ...],
) -> bool:
    """Return whether any attached decorator name satisfies *required* names/globs."""
    return any(att == req or fnmatch(att, req) for req in required for att in attached)


class ScopedCallRule(Rule):
    """Shared base for config-driven rules matching call targets in scoped files."""

    target_option_name: ClassVar[str]
    only_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()

    def __init__(self) -> None:
        setattr(self, self.target_option_name, ())
        self.only_paths = ()
        self.exclude_paths = ()

    @property
    def target_symbols(self) -> tuple[str, ...]:
        """Configured class or symbol names matched on call targets."""
        return tuple(getattr(self, self.target_option_name))

    def should_check_file(self, context: FileContext) -> bool:
        """Stay inert until target symbols are set and *context* is in scope."""
        if not self.target_symbols:
            return False
        return file_matches_scope(
            context,
            only_paths=self.only_paths,
            exclude_paths=self.exclude_paths,
        )

    def _configure_scoped_call(self, options: dict[str, Any]) -> None:
        apply_str_list_options(
            self,
            options,
            self.target_option_name,
            "only_paths",
            "exclude_paths",
        )

    def _matched_call_target(self, call_node: Node) -> str | None:
        candidates = call_target_candidates(call_node)
        if candidates is None:
            return None
        return match_configured_symbol(
            candidates[0], candidates[1], self.target_symbols
        )

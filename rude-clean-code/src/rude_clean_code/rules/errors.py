"""Fail-fast error handling Clean Code rules (CC309-CC311)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity
from rude.providers import ScopeProvider
from rude.providers.semantic import CTX_IN_EXCEPT

from rude_clean_code._scope import (
    SCOPE_BOUNDARY_TYPES,
    ThresholdRule,
    is_test_context,
    parse_bool_option,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

_BROAD_EXCEPTION_NAMES = frozenset({"Exception", "BaseException"})
_QUALIFIED_BROAD_EXCEPTIONS = frozenset(
    {"builtins.Exception", "builtins.BaseException"}
)
_NESTED_DEF_TYPES = frozenset(
    {"function_definition", "class_definition", "decorated_definition"}
)


def _match_broad_type(expr: Node) -> str | None:
    if expr.type == "as_pattern":
        children = expr.named_children
        return _match_broad_type(children[0]) if children else None
    if expr.type in {"tuple", "parenthesized_expression"}:
        return next(
            (m for item in expr.named_children if (m := _match_broad_type(item))),
            None,
        )
    is_broad = (expr.type == "identifier" and expr.text in _BROAD_EXCEPTION_NAMES) or (
        expr.type == "attribute" and expr.text in _QUALIFIED_BROAD_EXCEPTIONS
    )
    return expr.text if is_broad else None


def _caught_broad_exception(except_clause: Node) -> str | None:
    non_block = [
        child for child in except_clause.named_children if child.type != "block"
    ]
    if not non_block:
        return "bare except:"
    return _match_broad_type(non_block[0])


def _is_trivial_return(stmt: Node) -> str | None:
    children = stmt.named_children
    if not children:
        return "return"
    if len(children) != 1:
        return None
    value = children[0]
    is_trivial = value.type in {"none", "false"} or (
        value.type in {"list", "dictionary"} and not value.named_children
    )
    return f"return {value.text}" if is_trivial else None


def _trivial_stmt_label(stmt: Node) -> str | None:
    label: str | None = None
    if stmt.type == "pass_statement":
        label = "pass"
    elif stmt.type == "continue_statement":
        label = "continue"
    elif stmt.type == "expression_statement":
        children = stmt.named_children
        if len(children) == 1 and children[0].type == "ellipsis":
            label = "..."
    elif stmt.type == "return_statement":
        label = _is_trivial_return(stmt)
    return label


def _swallowed_handler_action(block: Node) -> str | None:
    stmts = [child for child in block.named_children if child.type != "comment"]
    if not stmts:
        return None
    last_label: str | None = None
    for stmt in stmts:
        label = _trivial_stmt_label(stmt)
        if label is None:
            return None
        last_label = label
    return last_label


def _is_directly_in_except_block(node: Node) -> bool:
    prev = node
    current = node.parent
    while current is not None:
        if current.type in SCOPE_BOUNDARY_TYPES:
            return False
        if current.type == "except_clause":
            children = current.named_children
            return bool(
                children and children[-1].type == "block" and prev == children[-1]
            )
        prev = current
        current = current.parent
    return False


def _nested_definition_lines(body: Node) -> set[int]:
    excluded: set[int] = set()
    stack = list(reversed(body.named_children))
    while stack:
        current = stack.pop()
        if current.type in _NESTED_DEF_TYPES:
            excluded.update(range(current.line, current.end_line + 1))
            continue
        stack.extend(reversed(current.named_children))
    return excluded


class BroadExceptionSwallowed(Rule):
    """CC309: Broad ``except`` clause silently swallows errors without recovery or logging."""

    code: ClassVar[str] = "CC309"
    message: ClassVar[str] = "Broad exception handler silently swallows errors"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.EXCEPT_CLAUSE}

    exclude_tests: bool = True

    def __init__(self) -> None:
        self.exclude_tests = True

    def should_check_file(self, context: FileContext) -> bool:
        """Skip test modules unless ``exclude_tests`` is disabled."""
        return not (self.exclude_tests and is_test_context(context))

    def configure(self, options: dict[str, Any]) -> None:
        """Configure test-file exclusion."""
        if "exclude_tests" in options:
            self.exclude_tests = parse_bool_option(
                self.code, "exclude_tests", options["exclude_tests"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag bare ``except:`` or ``Exception``/``BaseException`` handlers that swallow."""
        broad = _caught_broad_exception(node)
        if broad is None:
            return
        children = node.named_children
        if not children or children[-1].type != "block":
            return
        action = _swallowed_handler_action(children[-1])
        if action is None:
            return
        yield self.diagnostic(
            node,
            f"Broad exception handler ({broad}) swallows error via '{action}'; "
            "catch specific exceptions, log or re-raise, or use contextlib.suppress",
        )


class MissingExceptionChaining(Rule):
    """CC310: New exception raised inside an ``except`` block without ``from`` chaining."""

    code: ClassVar[str] = "CC310"
    message: ClassVar[str] = "Exception raised inside except without 'from' chaining"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.RAISE_STATEMENT}
    metadata_dependencies: ClassVar[set[type]] = {ScopeProvider}

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag non-bare ``raise`` inside ``except`` lacking ``from <cause>``."""
        if not node.named_children:
            return
        if any(child.type == "from" for child in node.children):
            return
        model = node.get_metadata(ScopeProvider).model
        in_except = (
            model.has_context(node.start_byte, CTX_IN_EXCEPT)
            if model.node_context(node.start_byte) is not None
            else True
        )
        if in_except and _is_directly_in_except_block(node):
            yield self.diagnostic(
                node,
                "Exception raised inside 'except' block without 'from' chaining; "
                "preserve context with 'raise ... from err' or 'raise ... from None'",
            )


class OversizedTryBlock(ThresholdRule):
    """CC311: ``try:`` suite spans too many lines, obscuring the failing operation."""

    code: ClassVar[str] = "CC311"
    message: ClassVar[str] = "Try block body spans too many lines"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.TRY_STATEMENT}
    option_name: ClassVar[str] = "max_lines"
    default_limit: ClassVar[int] = 20

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag ``try:`` suites exceeding ``max_lines`` excluding nested definitions."""
        body = node.child_by_field("body")
        if body is None:
            return
        excluded = _nested_definition_lines(body)
        try_lines = len(set(range(body.line, body.end_line + 1)) - excluded)
        yield from self.emit_if_exceeds(
            node,
            try_lines,
            f"Try block body spans too many lines ({try_lines} > {self.limit}); "
            "narrow the guarded suite to the statements expected to fail",
        )


ERROR_RULES: list[type[Rule]] = [
    BroadExceptionSwallowed,
    MissingExceptionChaining,
    OversizedTryBlock,
]

__all__ = [
    "ERROR_RULES",
    "BroadExceptionSwallowed",
    "MissingExceptionChaining",
    "OversizedTryBlock",
]

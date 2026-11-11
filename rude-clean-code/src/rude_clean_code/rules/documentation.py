"""Documentation, docstring accuracy, and dangling-string Clean Code rules (CC901, CC907-CC910)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity

from rude_clean_code._scope import (
    definition_name,
    is_test_context,
    iter_own_scope,
    node_decorators,
    parse_bool_option,
)
from rude_clean_code.rules._docstring_analysis import (
    extract_documented_params,
    has_returns_section,
    is_placeholder_docstring,
    iter_public_api_definitions,
)
from rude_clean_code.rules._parameter_analysis import (
    has_var_keyword_param,
    is_stub_body,
    parse_parameters,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

_STRING_TYPES = frozenset({"string", "concatenated_string"})
_ASSIGNMENT_TYPES = frozenset({"assignment", "augmented_assignment"})
_VOID_RETURN_TYPES = frozenset({"None", "NoReturn", "Never"})
_CONTROL_FLOW_CONTAINERS = frozenset(
    {
        "if_statement",
        "elif_clause",
        "else_clause",
        "try_statement",
        "except_clause",
        "finally_clause",
        "with_statement",
        "for_statement",
        "while_statement",
        "match_statement",
        "case_clause",
    }
)


class _PublicDocstringRule(Rule):
    """Shared module/class opt-out configuration and test exemption for docstring rules."""

    check_modules: bool = True
    check_classes: bool = True

    def __init__(self) -> None:
        self.check_modules = True
        self.check_classes = True

    def should_check_file(self, context: FileContext) -> bool:
        """Exempt test files from public-API docstring enforcement."""
        return not is_test_context(context)

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ``check_modules`` and ``check_classes`` toggles."""
        if "check_modules" in options:
            self.check_modules = parse_bool_option(
                self.code, "check_modules", options["check_modules"]
            )
        if "check_classes" in options:
            self.check_classes = parse_bool_option(
                self.code, "check_classes", options["check_classes"]
            )


def _prev_non_comment_sibling(node: Node) -> Node | None:
    prev = node.prev_sibling
    while prev is not None and prev.type == "comment":
        prev = prev.prev_sibling
    return prev


def _block_owner_allows_attr_doc(block: Node) -> bool | None:
    owner = block.parent
    if owner is None:
        return False
    if owner.type == "class_definition":
        return True
    if owner.type == "function_definition":
        return definition_name(owner) == "__init__"
    if owner.type in _CONTROL_FLOW_CONTAINERS:
        return None
    return False


def _is_attribute_doc_context(stmt: Node) -> bool:
    current = stmt.parent
    while current is not None:
        if current.type == "module":
            return True
        if current.type == "block":
            allowed = _block_owner_allows_attr_doc(current)
            if allowed is not None:
                return allowed
            current = current.parent.parent if current.parent is not None else None
            continue
        if current.type in _CONTROL_FLOW_CONTAINERS:
            current = current.parent
            continue
        return False
    return False


def _is_definition_docstring_stmt(stmt: Node) -> bool:
    parent = stmt.parent
    if parent is None:
        return False
    is_doc_container = parent.type == "module" or (
        parent.type == "block"
        and parent.parent_type in {"function_definition", "class_definition"}
    )
    if not is_doc_container:
        return False
    first = next((c for c in parent.named_children if c.type != "comment"), None)
    return first is not None and first.start_byte == stmt.start_byte


def _is_assignment_stmt(node: Node | None) -> bool:
    if node is None or node.type != "expression_statement" or not node.named_children:
        return False
    return node.named_children[0].type in _ASSIGNMENT_TYPES


def _has_yield_in_own_scope(body: Node) -> bool:
    return any(current.type == "yield" for current in iter_own_scope(body))


def _has_non_none_return(body: Node) -> bool:
    for current in iter_own_scope(body):
        if current.type != "return_statement":
            continue
        children = current.named_children
        if children and children[0].type != "none":
            return True
    return False


class MissingDocstring(_PublicDocstringRule):
    """CC901: Public module, class, or function is missing a docstring."""

    code: ClassVar[str] = "CC901"
    message: ClassVar[str] = "Public API definition is missing a docstring"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag public modules, classes, and functions lacking a leading docstring."""
        for kind, target in iter_public_api_definitions(
            node,
            check_modules=self.check_modules,
            check_classes=self.check_classes,
        ):
            if target.docstring() is not None:
                continue
            label = (
                target.ctx.path.name if kind == "module" else definition_name(target)
            )
            yield self.diagnostic(
                target,
                f"Public {kind} '{label}' is missing a docstring; add a docstring "
                "describing its purpose",
            )


class EmptyDocstring(_PublicDocstringRule):
    """CC907: Public docstring is empty, punctuation-only, or a TODO/FIXME placeholder."""

    code: ClassVar[str] = "CC907"
    message: ClassVar[str] = "Docstring is empty or a placeholder"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag blank, punctuation-only, or TODO-placeholder docstrings on public APIs."""
        for kind, target in iter_public_api_definitions(
            node,
            check_modules=self.check_modules,
            check_classes=self.check_classes,
        ):
            content = target.docstring()
            if content is None or not is_placeholder_docstring(content):
                continue
            label = (
                target.ctx.path.name if kind == "module" else definition_name(target)
            )
            yield self.diagnostic(
                target,
                f"Public {kind} '{label}' has an empty or placeholder docstring; "
                "replace with a meaningful summary or remove the stub",
            )


class DocstringParameterDrift(Rule):
    """CC908: Function docstring parameter section does not match its signature."""

    code: ClassVar[str] = "CC908"
    message: ClassVar[str] = "Docstring parameter list drifts from function signature"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}

    report_missing: bool = False

    def __init__(self) -> None:
        self.report_missing = False

    def configure(self, options: dict[str, Any]) -> None:
        """Configure whether undocumented signature parameters are reported too."""
        if "report_missing" in options:
            self.report_missing = parse_bool_option(
                self.code, "report_missing", options["report_missing"]
            )

    def _iter_missing_param_diags(
        self,
        node: Node,
        fn_name: str,
        specs: list[Any],
        doc_set: set[str],
    ) -> Iterator[Diagnostic]:
        for spec in specs:
            is_regular = not spec.is_variadic and spec.name not in {"self", "cls"}
            if is_regular and spec.name not in doc_set:
                yield self.diagnostic(
                    node,
                    f"Parameter '{spec.name}' of '{fn_name}' is omitted from its "
                    "docstring parameter section; document it or align Args",
                )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag phantom documented parameters (and missing ones if ``report_missing``)."""
        doc = node.docstring()
        if doc is None:
            return
        has_section, doc_params = extract_documented_params(doc)
        if not has_section:
            return
        specs = parse_parameters(node)
        sig_names = {spec.name for spec in specs}
        fn_name = definition_name(node)
        if not has_var_keyword_param(node):
            for name in doc_params:
                if name not in sig_names:
                    yield self.diagnostic(
                        node,
                        f"Docstring for '{fn_name}' documents phantom parameter "
                        f"'{name}' absent from signature; update docstring or signature",
                    )
        if self.report_missing:
            yield from self._iter_missing_param_diags(
                node, fn_name, specs, set(doc_params)
            )


class DocstringReturnYieldMismatch(Rule):
    """CC909: Docstring ``Returns:`` mismatches generator or void function body."""

    code: ClassVar[str] = "CC909"
    message: ClassVar[str] = (
        "Docstring Returns section conflicts with function return/yield behavior"
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag ``Returns:`` sections on generators or ``None``-only functions."""
        doc = node.docstring()
        if doc is None or not has_returns_section(doc):
            return
        if is_stub_body(node) or any(
            dec in {"abstractmethod", "overload"} for dec in node_decorators(node)
        ):
            return
        body = node.body
        if body is None:
            return
        fn_name = definition_name(node)
        if _has_yield_in_own_scope(body):
            yield self.diagnostic(
                node,
                f"Docstring for generator '{fn_name}' declares a Returns section; "
                "suggests using 'Yields:' instead",
            )
            return
        ret_type = node.child_by_field("return_type")
        if ret_type is not None and ret_type.text.strip() not in _VOID_RETURN_TYPES:
            return
        if not _has_non_none_return(body):
            yield self.diagnostic(
                node,
                f"Docstring for '{fn_name}' declares a Returns section, but the "
                "function only returns None; remove Returns or return a value",
            )


class DanglingStringLiteral(Rule):
    """CC910: Bare string literal statement that is neither a docstring nor an attribute doc."""

    code: ClassVar[str] = "CC910"
    message: ClassVar[str] = "Dangling string literal serves no docstring role"
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType] | None] = {NodeType.EXPRESSION_STATEMENT}

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag bare body string literals outside definition or attribute docstrings."""
        children = node.named_children
        if len(children) != 1 or children[0].type not in _STRING_TYPES:
            return
        if _is_definition_docstring_stmt(node):
            return
        if _is_attribute_doc_context(node) and _is_assignment_stmt(
            _prev_non_comment_sibling(node)
        ):
            return
        yield self.diagnostic(
            node,
            "Dangling string literal is neither a definition docstring nor an "
            "attribute docstring; convert to a '#' comment or assign to a name",
        )


DOCUMENTATION_RULES: list[type[Rule]] = [
    MissingDocstring,
    EmptyDocstring,
    DocstringParameterDrift,
    DocstringReturnYieldMismatch,
    DanglingStringLiteral,
]

__all__ = [
    "DOCUMENTATION_RULES",
    "DanglingStringLiteral",
    "DocstringParameterDrift",
    "DocstringReturnYieldMismatch",
    "EmptyDocstring",
    "MissingDocstring",
]

"""Module and package organization Clean Code rules (CC001-CC005)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity
from rude.providers import ScopeProvider

from rude_clean_code._scope import (
    ThresholdRule,
    is_dunder,
    is_test_context,
    matches_exclude_paths,
    parse_bool_option,
    parse_nonneg_int,
    parse_str_list_option,
)
from rude_clean_code.rules._module_analysis import (
    ALL_NAME,
    INIT_FILENAME,
    build_symbol_clusters,
    collect_init_exports,
    collect_top_level_defs,
    describe_non_facade_statement,
    extract_string_nodes,
    format_clusters,
    has_enclosing_scope_def,
    is_allowed_init_statement,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext
    from rude.providers.semantic import SemanticModel


class _PathFilteredRule(Rule):
    """Shared path and test-file exclusion filtering for module rules."""

    exclude_tests: bool = True
    exclude_paths: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.exclude_tests = True
        self.exclude_paths = ()

    def should_check_file(self, context: FileContext) -> bool:
        """Skip test modules or excluded path patterns according to options."""
        if self.exclude_tests and is_test_context(context):
            return False
        return not matches_exclude_paths(context, self.exclude_paths)

    def _configure_path_filters(self, options: dict[str, Any]) -> None:
        if "exclude_tests" in options:
            self.exclude_tests = parse_bool_option(
                self.code, "exclude_tests", options["exclude_tests"]
            )
        if "exclude_paths" in options:
            self.exclude_paths = parse_str_list_option(
                self.code, "exclude_paths", options["exclude_paths"]
            )


def _dominant_split_hint(
    defs: list[tuple[Node, Node, str]],
    total_lines: int,
    stem: str,
) -> str | None:
    for outer, target, name in defs:
        if outer.end_line - outer.line + 1 > total_lines / 2:
            rule_hint = "CC201" if target.type == "class_definition" else "CC101"
            kind = "class" if target.type == "class_definition" else "function"
            return (
                f"start with {rule_hint} on dominant {kind} '{name}', then split "
                f"'{stem}.py' into '{stem}/__init__.py' and focused submodules"
            )
    return None


class ModuleTooLarge(_PathFilteredRule):
    """CC001: Module line count exceeds threshold, with AST-derived split guidance."""

    code: ClassVar[str] = "CC001"
    name: ClassVar[str] = "module-too-large"
    message: ClassVar[str] = "Module exceeds maximum line count"
    description: ClassVar[str] = (
        "Modules should stay focused and small; split oversized modules along symbol boundaries."
    )
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType]] = {NodeType.MODULE}
    metadata_dependencies: ClassVar[set[type]] = {ScopeProvider}

    max_lines: int = 400

    def __init__(self) -> None:
        super().__init__()
        self.max_lines = 400

    def configure(self, options: dict[str, Any]) -> None:
        """Configure line limit, test-file exclusion, and excluded path globs."""
        self._configure_path_filters(options)
        if "max_lines" in options:
            self.max_lines = parse_nonneg_int(
                self.code, "max_lines", options["max_lines"]
            )

    def _split_suggestion(
        self,
        node: Node,
        total_lines: int,
        model: SemanticModel,
    ) -> str:
        stem = node.ctx.path.stem
        defs = collect_top_level_defs(node)
        dominant = _dominant_split_hint(defs, total_lines, stem)
        if dominant is not None:
            return dominant
        if node.ctx.path.name == INIT_FILENAME:
            return (
                "keep '__init__.py' as a re-export facade and move "
                "implementations into sibling submodules"
            )
        clusters = build_symbol_clusters(defs, model)
        if len(clusters) >= 2:
            summary = format_clusters(clusters)
            return (
                f"convert '{stem}.py' into '{stem}/__init__.py' (re-exporting "
                f"public symbols) and submodules for clusters ({summary})"
            )
        return (
            f"split '{stem}.py' into '{stem}/__init__.py' (re-exporting the "
            "public API) and smaller submodules"
        )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag modules exceeding ``max_lines`` with an AST-derived split plan."""
        total_lines = len(node.ctx.lines)
        if total_lines <= self.max_lines:
            return
        model = node.get_metadata(ScopeProvider).model
        suggestion = self._split_suggestion(node, total_lines, model)
        yield self.diagnostic(
            node,
            f"Module has too many lines ({total_lines} > {self.max_lines}); {suggestion}",
        )


class InitModuleContainsLogic(_PathFilteredRule):
    """CC002: ``__init__.py`` files should remain re-export facades without runtime logic."""

    code: ClassVar[str] = "CC002"
    name: ClassVar[str] = "init-module-contains-logic"
    message: ClassVar[str] = (
        "__init__.py should remain a re-export facade without runtime logic"
    )
    description: ClassVar[str] = (
        "Package __init__.py files should only expose public re-exports and metadata."
    )
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType]] = {NodeType.MODULE}

    allowed_names: tuple[str, ...] = ()
    allow_lazy_getattr: bool = True

    def __init__(self) -> None:
        super().__init__()
        self.allowed_names = ()
        self.allow_lazy_getattr = True

    def should_check_file(self, context: FileContext) -> bool:
        """Apply only to ``__init__.py`` files after shared exclusions."""
        if context.path.name != INIT_FILENAME:
            return False
        return super().should_check_file(context)

    def configure(self, options: dict[str, Any]) -> None:
        """Configure allowed metadata names, PEP 562 hooks, and exclusions."""
        self._configure_path_filters(options)
        if "allowed_names" in options:
            self.allowed_names = parse_str_list_option(
                self.code, "allowed_names", options["allowed_names"]
            )
        if "allow_lazy_getattr" in options:
            self.allow_lazy_getattr = parse_bool_option(
                self.code, "allow_lazy_getattr", options["allow_lazy_getattr"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag runtime definitions, control flow, and non-facade assignments in ``__init__.py``."""
        allowed = frozenset(self.allowed_names)
        seen_first = False
        for stmt in node.named_children:
            if stmt.type == "comment":
                continue
            is_first = not seen_first
            seen_first = True
            if is_allowed_init_statement(
                stmt,
                is_first,
                allowed,
                allow_lazy_getattr=self.allow_lazy_getattr,
            ):
                continue
            kind, label = describe_non_facade_statement(stmt)
            yield self.diagnostic(
                stmt,
                f"Non-facade {kind} '{label}' in '__init__.py'; move runtime logic "
                "into a submodule and re-export public symbols via '__all__'",
            )


class InitModuleMissingAll(_PathFilteredRule):
    """CC003: Non-empty ``__init__.py`` files must declare complete ``__all__`` exports."""

    code: ClassVar[str] = "CC003"
    name: ClassVar[str] = "init-module-missing-all"
    message: ClassVar[str] = "__init__.py must declare __all__ for public exports"
    description: ClassVar[str] = (
        "Non-empty __init__.py files must explicitly define __all__ and cover public re-exports."
    )
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType]] = {NodeType.MODULE}

    allow_empty: bool = True
    require_reexports_in_all: bool = True

    def __init__(self) -> None:
        super().__init__()
        self.allow_empty = True
        self.require_reexports_in_all = True

    def should_check_file(self, context: FileContext) -> bool:
        """Apply only to ``__init__.py`` files after shared exclusions."""
        if context.path.name != INIT_FILENAME:
            return False
        return super().should_check_file(context)

    def configure(self, options: dict[str, Any]) -> None:
        """Configure empty-marker allowance, re-export checks, and exclusions."""
        self._configure_path_filters(options)
        if "allow_empty" in options:
            self.allow_empty = parse_bool_option(
                self.code, "allow_empty", options["allow_empty"]
            )
        if "require_reexports_in_all" in options:
            self.require_reexports_in_all = parse_bool_option(
                self.code,
                "require_reexports_in_all",
                options["require_reexports_in_all"],
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag non-empty ``__init__.py`` missing ``__all__`` or omitting public re-exports."""
        has_runtime_content, all_exports, public_reexports = collect_init_exports(node)
        if not has_runtime_content:
            if not self.allow_empty:
                yield self.diagnostic(
                    node,
                    "Empty or marker '__init__.py' does not declare '__all__'; "
                    "define '__all__ = []' or remove unnecessary initializer",
                )
            return
        if all_exports is None:
            yield self.diagnostic(
                node,
                "Non-empty '__init__.py' is missing '__all__'; explicitly list "
                "all exported public names",
            )
            return
        if self.require_reexports_in_all:
            exported = set(all_exports)
            missing = [name for name in public_reexports if name not in exported]
            if missing:
                joined = ", ".join(missing)
                yield self.diagnostic(
                    node,
                    f"Public re-exports omitted from '__all__' ({joined}); add "
                    "them to '__all__' or alias internal imports with a leading '_'",
                )


class DeepRelativeImport(ThresholdRule):
    """CC004: Relative import depth exceeds maximum allowed parent hops."""

    code: ClassVar[str] = "CC004"
    name: ClassVar[str] = "deep-relative-import"
    message: ClassVar[str] = "Relative import spans too many parent packages"
    description: ClassVar[str] = (
        "Avoid deep relative imports spanning many parent packages; prefer absolute imports."
    )
    node_types: ClassVar[set[NodeType]] = {NodeType.IMPORT_FROM_STATEMENT}
    option_name: ClassVar[str] = "max_relative_depth"
    default_limit: ClassVar[int] = 2

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag ``from ... import`` statements exceeding ``max_relative_depth`` dots."""
        for child in node.named_children:
            if child.type != "relative_import":
                continue
            for part in child.named_children:
                if part.type == "import_prefix":
                    depth = len(part.text)
                    yield from self.emit_if_exceeds(
                        node,
                        depth,
                        f"Relative import depth ({depth} > {self.limit}) spans too "
                        "many package levels; replace with an absolute import",
                    )


class PrivateExportInAll(Rule):
    """CC005: Private ``_``-prefixed symbol exported in module-level ``__all__``."""

    code: ClassVar[str] = "CC005"
    name: ClassVar[str] = "private-export-in-all"
    message: ClassVar[str] = "Private _-prefixed symbol exported in __all__"
    description: ClassVar[str] = (
        "Module __all__ should expose only public API names, never private _-prefixed symbols."
    )
    severity: ClassVar[Severity | None] = Severity.WARNING
    node_types: ClassVar[set[NodeType]] = {
        NodeType.ASSIGNMENT,
        NodeType.AUGMENTED_ASSIGNMENT,
    }

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag ``_``-prefixed non-dunder string literals inside module-level ``__all__``."""
        if has_enclosing_scope_def(node):
            return
        left = node.child_by_field("left")
        right = node.child_by_field("right")
        if left is None or right is None:
            return
        if left.type != "identifier" or left.text != ALL_NAME:
            return
        for str_node, symbol in extract_string_nodes(right):
            if symbol.startswith("_") and not is_dunder(symbol):
                yield self.diagnostic(
                    str_node,
                    f"Private symbol '{symbol}' exported in '__all__'; remove it "
                    "from '__all__' or rename it without a leading underscore",
                )


MODULE_RULES: list[type[Rule]] = [
    ModuleTooLarge,
    InitModuleContainsLogic,
    InitModuleMissingAll,
    DeepRelativeImport,
    PrivateExportInAll,
]

__all__ = [
    "MODULE_RULES",
    "DeepRelativeImport",
    "InitModuleContainsLogic",
    "InitModuleMissingAll",
    "ModuleTooLarge",
    "PrivateExportInAll",
]

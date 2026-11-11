"""Parameter and signature Clean Code heuristic rules (CC105-CC106, CC108)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

from rude.core.node_types import NodeType
from rude.core.rule import Rule
from rude.core.types import Diagnostic, Severity
from rude.providers import NO_SCOPE, ScopeProvider

from rude_clean_code._scope import (
    definition_name,
    is_test_context,
    node_decorators,
    parse_bool_option,
    parse_min_int,
    parse_str_list_option,
)
from rude_clean_code.rules._parameter_analysis import (
    ParamSpec,
    is_bool_annotation,
    is_bool_default,
    is_stub_body,
    parse_parameters,
)

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.types import FileContext

DEFAULT_FLAG_NAMES: frozenset[str] = frozenset(
    {
        "allow_empty",
        "auto_commit",
        "confirm",
        "dry_run",
        "force",
        "ignore_errors",
        "in_place",
        "inplace",
        "overwrite",
        "quiet",
        "raise_on_error",
        "recursive",
        "silent",
        "skip_validation",
        "strict",
        "validate",
        "verbose",
    }
)
_EXEMPT_PARAM_DECORATORS = frozenset({"override", "abstractmethod", "overload"})
_SKIP_CLUMP_PARAMS = frozenset({"self", "cls", "args", "kwargs"})


def _flag_reason(spec: ParamSpec) -> str | None:
    has_type = is_bool_annotation(spec.type_node)
    has_default = is_bool_default(spec.default_node)
    if has_type and has_default:
        return "annotated bool with bool default"
    if has_type:
        return "annotated bool"
    if has_default:
        return "bool default"
    return None


def _nonlocal_names(body: Node) -> set[str]:
    names: set[str] = set()
    for current in body.walk():
        if current.type != "nonlocal_statement":
            continue
        for child in current.named_children:
            if child.type == "identifier" and child.text:
                names.add(child.text)
    return names


def _is_exempt_unused_param(
    spec: ParamSpec,
    prefixes: tuple[str, ...],
) -> bool:
    if spec.name in {"self", "cls"}:
        return True
    if spec.is_variadic and spec.name in {"args", "kwargs"}:
        return True
    return any(spec.name.startswith(prefix) for prefix in prefixes if prefix)


def _pairwise_candidate_sets(
    signatures: list[tuple[Node, str, frozenset[str]]],
    min_params: int,
) -> set[frozenset[str]]:
    candidates: set[frozenset[str]] = set()
    for idx, (_n1, _fn1, params1) in enumerate(signatures):
        for _n2, _fn2, params2 in signatures[idx + 1 :]:
            shared = params1 & params2
            if len(shared) >= min_params:
                candidates.add(shared)
    return candidates


def _maximal_clumps(
    signatures: list[tuple[Node, str, frozenset[str]]],
    min_params: int,
    min_functions: int,
) -> list[tuple[frozenset[str], list[tuple[Node, str]]]]:
    candidates = _pairwise_candidate_sets(signatures, min_params)
    frequent: list[tuple[frozenset[str], list[tuple[Node, str]]]] = []
    for subset in sorted(candidates, key=lambda s: (-len(s), sorted(s))):
        holders = [
            (fn, name) for fn, name, f_params in signatures if subset <= f_params
        ]
        if len(holders) < min_functions:
            continue
        if not any(subset < existing for existing, _ in frequent):
            frequent.append((subset, holders))
    return frequent


class BooleanFlagParameter(Rule):
    """CC105: Parameter appears to be a boolean mode switch splitting function behavior."""

    code: ClassVar[str] = "CC105"
    message: ClassVar[str] = "Parameter looks like a boolean mode flag"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}

    flag_names: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.flag_names = ()

    def configure(self, options: dict[str, Any]) -> None:
        """Extend the built-in mode-flag parameter vocabulary via ``flag_names``."""
        if "flag_names" in options:
            self.flag_names = parse_str_list_option(
                self.code, "flag_names", options["flag_names"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag boolean parameters whose name matches a mode-switch word."""
        vocab = DEFAULT_FLAG_NAMES | frozenset(item.lower() for item in self.flag_names)
        fn_name = definition_name(node)
        for spec in parse_parameters(node):
            if spec.is_variadic or spec.name in {"self", "cls"}:
                continue
            if spec.name.lstrip("_").lower() not in vocab:
                continue
            reason = _flag_reason(spec)
            if reason is None:
                continue
            yield self.diagnostic(
                spec.node,
                f"Parameter '{spec.name}' in '{fn_name}' looks like a boolean mode "
                f"flag ({reason}); suggests splitting into distinct functions instead "
                "of branching on a flag",
            )


class UnusedParameter(Rule):
    """CC106: Non-ignored parameter has no references in the function scope."""

    code: ClassVar[str] = "CC106"
    message: ClassVar[str] = "Function parameter is never used"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.FUNCTION_DEFINITION}
    metadata_dependencies: ClassVar[set[type]] = {ScopeProvider}

    ignore_prefixes: tuple[str, ...] = ("_",)
    exclude_tests: bool = True

    def __init__(self) -> None:
        self.ignore_prefixes = ("_",)
        self.exclude_tests = True

    def should_check_file(self, context: FileContext) -> bool:
        """Skip test modules unless ``exclude_tests`` is disabled."""
        return not (self.exclude_tests and is_test_context(context))

    def configure(self, options: dict[str, Any]) -> None:
        """Configure ignored parameter prefixes and test-file exclusion."""
        if "ignore_prefixes" in options:
            self.ignore_prefixes = parse_str_list_option(
                self.code, "ignore_prefixes", options["ignore_prefixes"]
            )
        if "exclude_tests" in options:
            self.exclude_tests = parse_bool_option(
                self.code, "exclude_tests", options["exclude_tests"]
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Flag unused function parameters outside stubs and exempt decorators."""
        if is_stub_body(node) or any(
            dec in _EXEMPT_PARAM_DECORATORS for dec in node_decorators(node)
        ):
            return
        model = node.get_metadata(ScopeProvider).model
        scope_id = model.scope_at(node)
        if scope_id == NO_SCOPE or scope_id >= len(model.scopes):
            return
        yield from self._unused_param_diagnostics(node, model, scope_id)

    def _unused_param_diagnostics(
        self, node: Node, model: Any, scope_id: int
    ) -> Iterator[Diagnostic]:
        scope = model.scopes[scope_id]
        nonlocals = _nonlocal_names(node.body) if node.body is not None else set()
        fn_name = definition_name(node)
        for spec in parse_parameters(node):
            if (
                _is_exempt_unused_param(spec, self.ignore_prefixes)
                or spec.name in nonlocals
            ):
                continue
            bid = scope.bindings.get(spec.name)
            if bid is None:
                continue
            binding = model.bindings[bid]
            if binding.is_parameter and not binding.is_used:
                yield self.diagnostic(
                    spec.node,
                    f"Parameter '{spec.name}' in '{fn_name}' appears unused; "
                    "remove it or prefix with '_' if required by a caller contract",
                )


class DataClump(Rule):
    """CC108: Shared parameter tuple recurs across multiple functions in one file."""

    code: ClassVar[str] = "CC108"
    message: ClassVar[str] = "Repeated parameter group suggests a parameter object"
    severity: ClassVar[Severity | None] = Severity.INFO
    node_types: ClassVar[set[NodeType] | None] = {NodeType.MODULE}

    min_params: int = 3
    min_functions: int = 3

    def __init__(self) -> None:
        self.min_params = 3
        self.min_functions = 3

    def configure(self, options: dict[str, Any]) -> None:
        """Configure minimum shared parameter count and minimum function occurrences."""
        if "min_params" in options:
            self.min_params = parse_min_int(
                self.code, "min_params", options["min_params"], 2
            )
        if "min_functions" in options:
            self.min_functions = parse_min_int(
                self.code, "min_functions", options["min_functions"], 2
            )

    def check(self, node: Node) -> Iterator[Diagnostic]:
        """Report maximal parameter sets recurring across multiple functions."""
        signatures: list[tuple[Node, str, frozenset[str]]] = []
        for fn in node.find("function_definition"):
            names = frozenset(
                spec.name
                for spec in parse_parameters(fn)
                if not spec.is_variadic and spec.name not in _SKIP_CLUMP_PARAMS
            )
            if len(names) >= self.min_params:
                signatures.append((fn, definition_name(fn), names))
        for subset, holders in _maximal_clumps(
            signatures, self.min_params, self.min_functions
        ):
            params_text = ", ".join(sorted(subset))
            fn_list = ", ".join(
                f"'{fn_name}' (line {fn_node.line})" for fn_node, fn_name in holders
            )
            yield self.diagnostic(
                holders[0][0],
                f"Parameter group ({params_text}; {len(subset)} >= {self.min_params}) "
                f"recurs across {len(holders)} >= {self.min_functions} functions in "
                f"this file ({fn_list}); suggests grouping into a dataclass or value object",
            )


FUNCTION_HEURISTIC_RULES: list[type[Rule]] = [
    BooleanFlagParameter,
    UnusedParameter,
    DataClump,
]

__all__ = [
    "DEFAULT_FLAG_NAMES",
    "FUNCTION_HEURISTIC_RULES",
    "BooleanFlagParameter",
    "DataClump",
    "UnusedParameter",
]

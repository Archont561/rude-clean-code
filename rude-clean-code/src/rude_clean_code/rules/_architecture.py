"""Shared config-driven layer specification and module import matching helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rude.core.types import Diagnostic

from rude_clean_code._scope import option_error, parse_str_list_option
from rude_clean_code.rules._symbol_matching import file_matches_scope

if TYPE_CHECKING:
    from rude.core.node import Node
    from rude.core.rule import Rule
    from rude.core.types import FileContext

_DICT_SOURCE_KEYS = ("from_paths", "only_paths", "from")
_DICT_TARGET_KEYS = ("forbidden_modules", "modules", "to")
_ALLOWED_LAYER_SPEC_KEYS = frozenset(
    {*_DICT_SOURCE_KEYS, *_DICT_TARGET_KEYS, "exclude_paths"}
)


@dataclass(frozen=True)
class LayerDependencySpec:
    """Immutable, pickleable path-to-forbidden-modules dependency specification."""

    only_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    forbidden_modules: tuple[str, ...] = ()

    def applies_to_file(self, context: FileContext) -> bool:
        """Return whether this rule applies to *context* and has modules to forbid."""
        if not self.forbidden_modules:
            return False
        return file_matches_scope(
            context,
            only_paths=self.only_paths,
            exclude_paths=self.exclude_paths,
        )


def any_spec_matches_file(
    context: FileContext,
    specs: Sequence[LayerDependencySpec],
) -> bool:
    """Return whether at least one dependency spec applies to *context*."""
    return any(spec.applies_to_file(context) for spec in specs)


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    """Return whether *module_name* equals *prefix* or names one of its submodules."""
    if prefix.endswith("."):
        return module_name.startswith(prefix)
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _matching_prefix(
    module_name: str,
    forbidden_modules: tuple[str, ...],
) -> str | None:
    is_relative = module_name.startswith(".")
    for prefix in forbidden_modules:
        if is_relative != prefix.startswith("."):
            continue
        if module_matches_prefix(module_name, prefix):
            return prefix
    return None


def _coerce_nonempty_str_tuple(
    code: str,
    option_name: str,
    raw: object,
) -> tuple[str, ...]:
    values = (
        (raw,)
        if isinstance(raw, str)
        else parse_str_list_option(code, option_name, raw)
    )
    if not values or any(not item.strip() for item in values):
        raise ValueError(
            f"{code} option '{option_name}' entries must be non-empty strings, got {raw!r}"
        )
    return values


def parse_optional_str_or_list_option(
    code: str,
    option_name: str,
    raw: object,
) -> tuple[str, ...]:
    """Validate an optional string or list-of-strings option."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        if not raw.strip():
            raise ValueError(
                f"{code} option '{option_name}' must not be an empty string"
            )
        return (raw,)
    values = parse_str_list_option(code, option_name, raw)
    if any(not item.strip() for item in values):
        raise ValueError(
            f"{code} option '{option_name}' entries must be non-empty strings, got {raw!r}"
        )
    return values


def _pick_single_group(
    code: str,
    option_name: str,
    entry: dict[object, object],
    keys: tuple[str, ...],
    label: str,
) -> tuple[str, ...]:
    present = [key for key in keys if key in entry]
    if len(present) != 1:
        raise ValueError(
            f"{code} option '{option_name}' entry must specify one {label} key "
            f"from {keys}, got {entry!r}"
        )
    return _coerce_nonempty_str_tuple(code, option_name, entry[present[0]])


def _parse_dict_layer_spec(
    code: str,
    option_name: str,
    entry: dict[object, object],
) -> LayerDependencySpec:
    unknown = set(entry) - _ALLOWED_LAYER_SPEC_KEYS
    if unknown:
        raise ValueError(
            f"{code} option '{option_name}' entry has unknown keys "
            f"{sorted(str(k) for k in unknown)!r}"
        )
    only_paths = _pick_single_group(
        code, option_name, entry, _DICT_SOURCE_KEYS, "source path"
    )
    forbidden_modules = _pick_single_group(
        code, option_name, entry, _DICT_TARGET_KEYS, "forbidden module"
    )
    exclude_paths = (
        parse_str_list_option(code, "exclude_paths", entry["exclude_paths"])
        if "exclude_paths" in entry
        else ()
    )
    return LayerDependencySpec(
        only_paths=only_paths,
        exclude_paths=exclude_paths,
        forbidden_modules=forbidden_modules,
    )


def parse_layer_specs(
    code: str,
    option_name: str,
    raw: object,
) -> tuple[LayerDependencySpec, ...]:
    """Validate and freeze ``CC704`` layer-to-module dependency rules."""
    if not isinstance(raw, (list, tuple)):
        raise option_error(code, option_name, "a list of rule entries", raw)
    specs: list[LayerDependencySpec] = []
    for entry in raw:
        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            specs.append(
                LayerDependencySpec(
                    only_paths=_coerce_nonempty_str_tuple(code, option_name, entry[0]),
                    forbidden_modules=_coerce_nonempty_str_tuple(
                        code, option_name, entry[1]
                    ),
                )
            )
        elif isinstance(entry, dict):
            specs.append(_parse_dict_layer_spec(code, option_name, entry))
        else:
            raise ValueError(
                f"{code} option '{option_name}' entry must be a [from, module] pair "
                f"or mapping, got {entry!r}"
            )
    return tuple(specs)


def _imported_member_name(child: Node) -> str | None:
    if child.type == "dotted_name":
        return child.text
    if child.type == "aliased_import":
        target = child.child_by_field("name")
        return target.text if target is not None else None
    return None


def _combine_from_member(base_mod: str, member: str) -> str:
    return f"{base_mod}{member}" if base_mod.endswith(".") else f"{base_mod}.{member}"


def _iter_import_from_targets(
    node: Node,
) -> Iterator[tuple[Node, str, tuple[tuple[Node, str], ...]]]:
    children = node.named_children
    if not children:
        return
    first = children[0]
    if first.type not in {"dotted_name", "relative_import"} or not first.text:
        return
    base_mod = first.text
    sub_targets = tuple(
        (child, _combine_from_member(base_mod, name))
        for child in children[1:]
        if (name := _imported_member_name(child)) is not None
    )
    yield (node, base_mod, sub_targets)


def _iter_import_targets(
    node: Node,
) -> Iterator[tuple[Node, str, tuple[tuple[Node, str], ...]]]:
    if node.type == "import_from_statement":
        yield from _iter_import_from_targets(node)
        return
    if node.type == "import_statement":
        for child in node.named_children:
            name = _imported_member_name(child)
            if name:
                yield (child, name, ())


def check_import_against_specs(
    rule: Rule,
    node: Node,
    specs: Sequence[LayerDependencySpec],
    format_message: Callable[[str, str, LayerDependencySpec], str],
) -> Iterator[Diagnostic]:
    """Check an import AST node against *specs* using shared module/path matching."""
    active_specs = [spec for spec in specs if spec.applies_to_file(node.ctx)]
    if not active_specs:
        return
    for target_node, module_name, sub_targets in _iter_import_targets(node):
        diag = _match_module_across_specs(
            rule, target_node, module_name, active_specs, format_message
        )
        if diag is not None:
            yield diag
            continue
        yield from _match_subtargets_across_specs(
            rule, sub_targets, active_specs, format_message
        )


def _match_module_across_specs(
    rule: Rule,
    target_node: Node,
    module_name: str,
    active_specs: Sequence[LayerDependencySpec],
    format_message: Callable[[str, str, LayerDependencySpec], str],
) -> Diagnostic | None:
    for spec in active_specs:
        matched = _matching_prefix(module_name, spec.forbidden_modules)
        if matched is not None:
            return rule.diagnostic(
                target_node,
                format_message(module_name, matched, spec),
            )
    return None


def _match_subtargets_across_specs(
    rule: Rule,
    sub_targets: tuple[tuple[Node, str], ...],
    active_specs: Sequence[LayerDependencySpec],
    format_message: Callable[[str, str, LayerDependencySpec], str],
) -> Iterator[Diagnostic]:
    for sub_node, sub_module in sub_targets:
        diag = _match_module_across_specs(
            rule, sub_node, sub_module, active_specs, format_message
        )
        if diag is not None:
            yield diag

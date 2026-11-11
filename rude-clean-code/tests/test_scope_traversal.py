"""Unit tests for shared own-scope AST traversal helpers."""

from __future__ import annotations

from pathlib import Path

from rude import FileContext, Node, parse
from rude.testing import check_source

from rude_clean_code._scope import iter_own_scope, max_own_scope_depth
from rude_clean_code.plugin import RULES


def _parse_first_function(source: str) -> Node:
    raw = source.encode("utf-8")
    tree = parse(raw)
    ctx = FileContext(Path("<test>"), raw, tree)
    root = Node(tree.root_node, ctx)
    fn = root.find_first("function_definition")
    assert fn is not None
    return fn


def test_iter_own_scope_excludes_nested_functions_classes_and_lambdas() -> None:
    source = """
def outer():
    x = 1
    @dec(outer_arg)
    def inner():
        y = 2
        return y
    class Nested:
        def method(self):
            return 3
    fn = lambda z: z + 4
    return x
"""
    fn = _parse_first_function(source)
    assert fn.body is not None
    own_types = [node.type for node in iter_own_scope(fn.body)]
    identifiers = [
        node.text for node in iter_own_scope(fn.body) if node.type == "identifier"
    ]
    assert own_types.count("return_statement") == 1
    assert "dec" in identifiers
    assert "outer_arg" in identifiers
    assert "fn" in identifiers
    assert "inner" not in identifiers
    assert "Nested" not in identifiers
    assert "y" not in identifiers
    assert "z" not in identifiers
    assert "method" not in identifiers


def test_max_own_scope_depth_respects_boundaries_and_elif_chains() -> None:
    source = """
def outer(flag, items):
    if flag:
        for item in items:
            pass
    elif len(items) > 1:
        pass
    else:
        pass
    def deep_inner():
        if True:
            if True:
                if True:
                    if True:
                        pass
"""
    fn = _parse_first_function(source)
    assert fn.body is not None
    control_types = frozenset(
        {
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement",
            "with_statement",
            "match_statement",
        }
    )
    assert max_own_scope_depth(fn.body, control_types) == 2


def test_rules_tolerate_incomplete_syntax_without_crashing() -> None:
    incomplete_sources = (
        "def incomplete(\n",
        "class Incomplete(\n",
        "x = a and\n",
    )
    for source in incomplete_sources:
        for rule_cls in RULES:
            filename = (
                "pkg/__init__.py"
                if rule_cls.code in {"CC002", "CC003"}
                else "pkg/sample.py"
            )
            diagnostics = check_source(rule_cls, source, filename=filename)
            assert any(diag.code == "E999" for diag in diagnostics)

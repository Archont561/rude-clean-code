"""Unit and integration tests for CC001-CC005 module organization rules."""

from __future__ import annotations

from pathlib import Path

import pytest
from rude.core.types import Severity
from rude.testing import (
    assert_error_count,
    assert_no_errors,
    assert_no_fix,
    check_source,
)

from rude_clean_code.rules.modules import (
    DeepRelativeImport,
    InitModuleContainsLogic,
    InitModuleMissingAll,
    ModuleTooLarge,
    PrivateExportInAll,
)


def _make_lines(count: int, line: str = "x = 1") -> str:
    return "\n".join(line for _ in range(count)) + "\n"


def _make_clustered_module(total_lines: int) -> str:
    parts = [
        "def _parse_alpha():",
        "    return 1",
        "",
        "def run_alpha():",
        "    return _parse_alpha()",
        "",
        "class BetaService:",
        "    def execute(self):",
        "        return 2",
        "",
        "def run_beta():",
        "    return BetaService().execute()",
        "",
    ]
    padding = total_lines - len(parts)
    if padding > 0:
        parts.extend(f"CONST_{idx} = {idx}" for idx in range(padding))
    return "\n".join(parts) + "\n"


def test_cc001_clean_and_violating_with_cluster_suggestions_and_no_fix() -> None:
    assert_no_errors(ModuleTooLarge, _make_lines(400), filename="pkg/service.py")
    diags = assert_error_count(
        ModuleTooLarge, _make_clustered_module(405), 1, filename="pkg/service.py"
    )
    assert diags[0].code == "CC001"
    assert diags[0].severity == Severity.WARNING
    msg = diags[0].message
    assert "405 > 400" in msg
    assert "service/__init__.py" in msg
    assert "run_alpha" in msg or "_parse_alpha" in msg
    assert "BetaService" in msg or "run_beta" in msg
    assert_no_fix(
        ModuleTooLarge, _make_clustered_module(405), filename="pkg/service.py"
    )


def test_cc001_dominant_class_suggestion() -> None:
    big_class = (
        "class Monolith:\n" + "\n".join(f"    a_{i} = {i}" for i in range(45)) + "\n"
    )
    class_diags = assert_error_count(
        ModuleTooLarge,
        big_class,
        1,
        options={"max_lines": 30},
        filename="pkg/monolith.py",
    )
    assert "CC201" in class_diags[0].message
    assert "Monolith" in class_diags[0].message


def test_cc001_dominant_function_and_init_suggestions() -> None:
    big_fn = "def giant():\n" + "\n".join(f"    v_{i} = {i}" for i in range(45)) + "\n"
    fn_diags = assert_error_count(
        ModuleTooLarge,
        big_fn,
        1,
        options={"max_lines": 30},
        filename="pkg/giant.py",
    )
    assert "CC101" in fn_diags[0].message
    assert "giant" in fn_diags[0].message

    init_diags = assert_error_count(
        ModuleTooLarge,
        _make_lines(35),
        1,
        options={"max_lines": 30},
        filename="pkg/__init__.py",
    )
    assert "sibling" in init_diags[0].message.lower()


def test_cc001_excludes_tests_and_configured_paths() -> None:
    assert_no_errors(
        ModuleTooLarge,
        _make_lines(450),
        filename="tests/test_big.py",
    )
    assert_error_count(
        ModuleTooLarge,
        _make_lines(450),
        1,
        options={"exclude_tests": False},
        filename="tests/test_big.py",
    )
    assert_no_errors(
        ModuleTooLarge,
        _make_lines(450),
        options={"exclude_paths": ["automation/dodo.py"]},
        filename="automation/dodo.py",
    )


def test_cc002_only_checks_init_and_permits_facade_constructs() -> None:
    assert_no_errors(
        InitModuleContainsLogic,
        "def regular_fn():\n    return 1\n",
        filename="pkg/module.py",
    )
    clean_init = (
        '"""Package facade."""\n'
        "from __future__ import annotations\n"
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from .types import Item\n"
        "from .core import Engine\n"
        '__version__ = "0.1.0"\n'
        '__all__ = ["Engine"]\n'
        "__all__ += []\n"
        "def __getattr__(name: str):\n"
        "    raise AttributeError(name)\n"
        "def __dir__() -> list[str]:\n"
        "    return list(__all__)\n"
    )
    assert_no_errors(InitModuleContainsLogic, clean_init, filename="pkg/__init__.py")


def test_cc002_flags_runtime_logic_and_respects_lazy_getattr_option() -> None:
    violating_init = (
        '"""Bad init."""\n'
        "from .core import Engine\n"
        '__all__ = ["Engine", "helper", "Service"]\n'
        "def helper():\n"
        "    return 1\n"
        "class Service:\n"
        "    pass\n"
        "if True:\n"
        "    pass\n"
        'CONFIG = {"a": 1}\n'
        'print("side effect")\n'
    )
    diags = assert_error_count(
        InitModuleContainsLogic, violating_init, 5, filename="pkg/__init__.py"
    )
    assert all(d.code == "CC002" and d.severity == Severity.INFO for d in diags)

    assert_error_count(
        InitModuleContainsLogic,
        "def __getattr__(name):\n    return name\n",
        1,
        options={"allow_lazy_getattr": False},
        filename="pkg/__init__.py",
    )


def test_cc002_verifies_package_init_with_and_without_allowed_names() -> None:
    pkg_init = (
        Path(__file__).resolve().parents[1] / "src" / "rude_clean_code" / "__init__.py"
    ).read_text(encoding="utf-8")

    diags = assert_error_count(
        InitModuleContainsLogic, pkg_init, 1, filename="src/rude_clean_code/__init__.py"
    )
    assert diags[0].severity == Severity.INFO
    assert "VERSION" in diags[0].message

    assert_no_errors(
        InitModuleContainsLogic,
        pkg_init,
        options={"allowed_names": ["VERSION"]},
        filename="src/rude_clean_code/__init__.py",
    )


def test_cc002_excludes_tests_and_configured_paths() -> None:
    assert_no_errors(
        InitModuleContainsLogic,
        "def helper():\n    return 1\n",
        filename="tests/__init__.py",
    )
    assert_error_count(
        InitModuleContainsLogic,
        "def helper():\n    return 1\n",
        1,
        options={"exclude_tests": False},
        filename="tests/__init__.py",
    )
    assert_no_errors(
        InitModuleContainsLogic,
        "def helper():\n    return 1\n",
        options={"exclude_paths": ["pkg/sub/__init__.py"]},
        filename="pkg/sub/__init__.py",
    )


def test_cc003_markers_and_package_initializers() -> None:
    assert_no_errors(InitModuleMissingAll, "x = 1\n", filename="pkg/mod.py")
    assert_no_errors(InitModuleMissingAll, "", filename="pkg/__init__.py")
    assert_no_errors(
        InitModuleMissingAll, '"""Marker package."""\n', filename="pkg/__init__.py"
    )
    assert_error_count(
        InitModuleMissingAll,
        '"""Marker package."""\n',
        1,
        options={"allow_empty": False},
        filename="pkg/__init__.py",
    )
    pkg_root = Path(__file__).resolve().parents[1] / "src" / "rude_clean_code"
    assert_no_errors(
        InitModuleMissingAll,
        (pkg_root / "__init__.py").read_text(encoding="utf-8"),
        filename="src/rude_clean_code/__init__.py",
    )
    rules_init = (pkg_root / "rules" / "__init__.py").read_text(encoding="utf-8")
    assert_no_errors(
        InitModuleContainsLogic,
        rules_init,
        filename="src/rude_clean_code/rules/__init__.py",
    )
    assert_no_errors(
        InitModuleMissingAll,
        rules_init,
        filename="src/rude_clean_code/rules/__init__.py",
    )


def test_cc003_flags_missing_all_and_omitted_reexports() -> None:
    diags = assert_error_count(
        InitModuleMissingAll,
        "from .core import PublicApi\n",
        1,
        filename="pkg/__init__.py",
    )
    assert diags[0].code == "CC003"
    assert diags[0].severity == Severity.WARNING
    assert "__all__" in diags[0].message

    clean_tc = (
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from .types import Hidden\n"
        "from .core import PublicA\n"
        '__all__ = ["PublicA"]\n'
    )
    assert_no_errors(InitModuleMissingAll, clean_tc, filename="pkg/__init__.py")


def test_cc003_flags_omitted_reexports_when_required() -> None:
    omitted = 'from .core import PublicA, PublicB\n__all__ = ["PublicA"]\n'
    reexport_diags = assert_error_count(
        InitModuleMissingAll, omitted, 1, filename="pkg/__init__.py"
    )
    assert "PublicB" in reexport_diags[0].message
    assert_no_errors(
        InitModuleMissingAll,
        omitted,
        options={"require_reexports_in_all": False},
        filename="pkg/__init__.py",
    )


def test_cc003_excludes_tests_and_paths() -> None:
    assert_no_errors(
        InitModuleMissingAll, "from .a import helper\n", filename="tests/__init__.py"
    )
    assert_error_count(
        InitModuleMissingAll,
        "from .a import helper\n",
        1,
        options={"exclude_tests": False},
        filename="tests/__init__.py",
    )
    assert_no_errors(
        InitModuleMissingAll,
        "from .a import helper\n",
        options={"exclude_paths": ["vendor/"]},
        filename="vendor/pkg/__init__.py",
    )


def test_cc004_deep_relative_imports() -> None:
    clean = (
        "from pkg.sub import item\n"
        "from . import sibling\n"
        "from ..parent import parent_obj\n"
    )
    assert_no_errors(DeepRelativeImport, clean)

    diags = assert_error_count(
        DeepRelativeImport,
        "from ...grandparent.mod import thing\nfrom .... import top\n",
        2,
    )
    assert diags[0].code == "CC004"
    assert diags[0].severity == Severity.WARNING
    assert "3 > 2" in diags[0].message
    assert "4 > 2" in diags[1].message

    assert_error_count(
        DeepRelativeImport,
        "from ..parent import x\n",
        1,
        options={"max_relative_depth": 1},
    )


def test_cc005_private_exports_in_all_and_dunder_exemption() -> None:
    clean = (
        '__all__ = ["Public", "__version__", "public_fn"]\n'
        '__all__ += ["Another"]\n'
        "def scoped():\n"
        '    __all__ = ["_not_module_level"]\n'
        "    return __all__\n"
    )
    assert_no_errors(PrivateExportInAll, clean)

    violating = (
        '__all__: list[str] = ["Public", "_helper", "__version__"]\n'
        '__all__ += ["_secret"]\n'
    )
    diags = sorted(
        assert_error_count(PrivateExportInAll, violating, 2),
        key=lambda d: (d.location.line, d.location.column),
    )
    assert diags[0].code == "CC005"
    assert diags[0].severity == Severity.WARNING
    assert "_helper" in diags[0].message
    assert "_secret" in diags[1].message


@pytest.mark.parametrize(
    ("rule_cls", "option", "bad_value"),
    [
        (ModuleTooLarge, "max_lines", -1),
        (ModuleTooLarge, "max_lines", True),
        (ModuleTooLarge, "exclude_tests", "yes"),
        (ModuleTooLarge, "exclude_paths", "not-a-list"),
        (InitModuleContainsLogic, "allowed_names", "VERSION"),
        (InitModuleContainsLogic, "allow_lazy_getattr", 1),
        (InitModuleMissingAll, "allow_empty", "true"),
        (InitModuleMissingAll, "require_reexports_in_all", 0),
        (DeepRelativeImport, "max_relative_depth", False),
    ],
)
def test_cc0xx_invalid_options_raise_value_error(
    rule_cls: type, option: str, bad_value: object
) -> None:
    rule = rule_cls()
    with pytest.raises(ValueError, match=option):
        rule.configure({option: bad_value})


def test_cc001_incomplete_syntax_handled_cleanly() -> None:
    diags = check_source(ModuleTooLarge, "def broken(\n", options={"max_lines": 0})
    codes = {d.code for d in diags}
    assert "E999" in codes


def test_cc001_decorator_links_cluster_via_module_scope_uses() -> None:
    source = (
        "def shared_dec(fn):\n"
        "    return fn\n\n"
        "@shared_dec\n"
        "def decorated_api():\n"
        "    return 1\n\n"
        "def other_one():\n"
        "    return 2\n\n"
        "def other_two():\n"
        "    return other_one()\n"
    )
    diags = assert_error_count(
        ModuleTooLarge,
        source,
        1,
        options={"max_lines": 5},
        filename="pkg/clustered.py",
    )
    assert "shared_dec/decorated_api" in diags[0].message
    assert "other_one/other_two" in diags[0].message

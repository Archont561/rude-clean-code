"""Rude entry-point module exposing implemented Clean Code rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rude_clean_code.rules.class_heuristics import CLASS_HEURISTIC_RULES
from rude_clean_code.rules.classes import CLASS_RULES
from rude_clean_code.rules.comments import COMMENT_RULES
from rude_clean_code.rules.complexity import COMPLEXITY_RULES
from rude_clean_code.rules.complexity_heuristics import COMPLEXITY_HEURISTIC_RULES
from rude_clean_code.rules.coupling_heuristics import COUPLING_HEURISTIC_RULES
from rude_clean_code.rules.dependencies import DEPENDENCY_RULES
from rude_clean_code.rules.documentation import DOCUMENTATION_RULES
from rude_clean_code.rules.dry import DRY_RULES
from rude_clean_code.rules.dry_heuristics import DRY_HEURISTIC_RULES
from rude_clean_code.rules.errors import ERROR_RULES
from rude_clean_code.rules.function_heuristics import FUNCTION_HEURISTIC_RULES
from rude_clean_code.rules.functions import FUNCTION_RULES
from rude_clean_code.rules.heuristics import HEURISTIC_RULES
from rude_clean_code.rules.modules import MODULE_RULES
from rude_clean_code.rules.naming import NAMING_RULES
from rude_clean_code.rules.patterns import PATTERN_RULES
from rude_clean_code.rules.solid_heuristics import SOLID_HEURISTIC_RULES

if TYPE_CHECKING:
    from rude.core.rule import Rule

RULES: list[type[Rule]] = [
    *MODULE_RULES,
    *FUNCTION_RULES,
    *FUNCTION_HEURISTIC_RULES,
    *CLASS_RULES,
    *CLASS_HEURISTIC_RULES,
    *COMPLEXITY_RULES,
    *COMPLEXITY_HEURISTIC_RULES,
    *ERROR_RULES,
    *NAMING_RULES,
    *DRY_RULES,
    *DRY_HEURISTIC_RULES,
    *HEURISTIC_RULES,
    *SOLID_HEURISTIC_RULES,
    *COUPLING_HEURISTIC_RULES,
    *DEPENDENCY_RULES,
    *PATTERN_RULES,
    *DOCUMENTATION_RULES,
    *COMMENT_RULES,
]

__all__ = ["RULES"]

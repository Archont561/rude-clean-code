"""Rude entry-point module exposing implemented Clean Code rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rude_clean_code.rules.classes import CLASS_RULES
from rude_clean_code.rules.complexity import COMPLEXITY_RULES
from rude_clean_code.rules.dry import DRY_RULES
from rude_clean_code.rules.errors import ERROR_RULES
from rude_clean_code.rules.functions import FUNCTION_RULES
from rude_clean_code.rules.heuristics import HEURISTIC_RULES
from rude_clean_code.rules.modules import MODULE_RULES
from rude_clean_code.rules.naming import NAMING_RULES

if TYPE_CHECKING:
    from rude.core.rule import Rule

RULES: list[type[Rule]] = [
    *MODULE_RULES,
    *FUNCTION_RULES,
    *CLASS_RULES,
    *COMPLEXITY_RULES,
    *ERROR_RULES,
    *NAMING_RULES,
    *DRY_RULES,
    *HEURISTIC_RULES,
]

__all__ = ["RULES"]

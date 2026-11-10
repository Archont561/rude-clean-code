"""Rude entry-point module exposing implemented Clean Code rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rude_clean_code.rules.classes import CLASS_RULES
from rude_clean_code.rules.complexity import COMPLEXITY_RULES
from rude_clean_code.rules.functions import FUNCTION_RULES

if TYPE_CHECKING:
    from rude.core.rule import Rule

RULES: list[type[Rule]] = [
    *FUNCTION_RULES,
    *CLASS_RULES,
    *COMPLEXITY_RULES,
]

__all__ = ["RULES"]

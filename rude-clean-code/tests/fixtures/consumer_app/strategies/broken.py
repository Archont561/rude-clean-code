"""Strategy implementations violating base or required-method contracts."""

from __future__ import annotations

from .base import PaymentStrategy


class UnboundStrategy:
    """Defines pay() without inheriting PaymentStrategy."""

    def pay(self, amount: int) -> bool:
        """Return positive check."""
        return amount > 0


class IncompleteStrategy(PaymentStrategy):
    """Inherits PaymentStrategy without defining pay()."""

    def validate(self, amount: int) -> bool:
        """Validate amount only."""
        return amount >= 0

"""Clean strategy implementation following the strategy protocol."""

from __future__ import annotations

from .base import PaymentStrategy


class CardStrategy(PaymentStrategy):
    """Concrete card strategy inheriting PaymentStrategy and implementing pay."""

    def pay(self, amount: int) -> bool:
        """Authorize a card payment."""
        return amount > 0

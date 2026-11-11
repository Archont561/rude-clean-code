"""Strategy protocol definition living inside the strategies package."""

from __future__ import annotations

from typing import Protocol


class PaymentStrategy(Protocol):
    """Base strategy contract implemented by concrete payment methods."""

    def pay(self, amount: int) -> bool:
        """Process *amount* in minor currency units."""

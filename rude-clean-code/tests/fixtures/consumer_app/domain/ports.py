"""Clean domain ports with no infrastructure dependencies."""

from __future__ import annotations

from typing import Protocol


class OrderRepository(Protocol):
    """Port implemented by infrastructure repositories."""

    def save(self, order_id: str) -> None:
        """Persist an order."""

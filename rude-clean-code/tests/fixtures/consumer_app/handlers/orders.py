"""Handler module containing registered, private-helper, and unregistered handlers."""

from __future__ import annotations

from app_framework import register_handler


@register_handler
def handle_create_order(order_id: str) -> str:
    """Registered handler with a nested helper."""

    def format_id(raw: str) -> str:
        return raw.strip().upper()

    return _normalize(format_id(order_id))


def _normalize(value: str) -> str:
    return value.replace(" ", "-")


def handle_cancel_order(order_id: str) -> str:
    """Public top-level handler missing the registration decorator."""
    return _normalize(order_id)

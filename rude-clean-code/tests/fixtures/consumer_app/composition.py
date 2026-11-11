"""Composition root excluded from direct-construction restrictions."""

from __future__ import annotations

from app_infra.repos import SqlOrderRepo
from billing.gateways import StripeGateway
from notifications.email import EmailNotifier


def build_runtime(api_key: str) -> tuple[SqlOrderRepo, StripeGateway, EmailNotifier]:
    """Assemble concrete collaborators at the application composition root."""
    return (
        SqlOrderRepo(),
        StripeGateway(api_key),
        EmailNotifier(),
    )

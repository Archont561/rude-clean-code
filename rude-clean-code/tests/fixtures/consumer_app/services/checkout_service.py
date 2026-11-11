"""Application service mixing clean DI/create_* usage with pattern violations."""

from __future__ import annotations

from billing.gateways import StripeGateway
from notifications.email import EmailNotifier
from sqlalchemy.orm import Session


def create_gateway(api_key: str) -> StripeGateway:
    """Factory function allowed by CC802 to instantiate product classes."""
    return StripeGateway(api_key)


class CheckoutService:
    """Service with one clean constructor-injected dependency and three violations."""

    def __init__(self, notifier: EmailNotifier | None = None) -> None:
        self.notifier = notifier or EmailNotifier()

    def checkout(self, session: Session, api_key: str) -> object:
        """Directly construct gateway and reference ORM session outside repos."""
        gateway = StripeGateway(api_key)
        return (session, gateway, self.notifier)

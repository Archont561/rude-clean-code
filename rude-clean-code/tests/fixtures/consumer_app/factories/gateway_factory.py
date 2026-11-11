"""Clean factory module constructing configured product classes."""

from __future__ import annotations

from billing.gateways import StripeGateway


class GatewayFactory:
    """Legitimate factory location for instantiating payment gateways."""

    def build(self, api_key: str) -> StripeGateway:
        """Create and return a configured gateway instance."""
        return StripeGateway(api_key)

"""Clean repository layer importing ORM modules legitimately."""

from __future__ import annotations

import sqlalchemy
from sqlalchemy.orm import Session


class SqlOrderRepo:
    """Repository implementation permitted to depend on SQLAlchemy."""

    def __init__(self, dsn: str) -> None:
        self.engine = sqlalchemy.create_engine(dsn)

    def save(self, order_id: str) -> Session:
        """Open a session for persistence."""
        return Session(self.engine, info={"order_id": order_id})

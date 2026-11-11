"""Domain module mixing clean port usage with forbidden infra coupling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import app_infra.postgres as pg
import sqlalchemy
from app_infra.repos import SqlOrderRepo
from boto3 import client
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from .ports import OrderRepository


def load_order_bad(dsn: str, bucket: str) -> tuple[object, object, object]:
    """Demonstrate forbidden ORM/SDK imports and direct repo instantiation."""
    engine = sqlalchemy.create_engine(dsn)
    session = Session(engine)
    s3 = client("s3")
    conn = pg.connect(bucket)
    repo = SqlOrderRepo()
    return (session, s3, (conn, repo))


def load_order_clean(repo: OrderRepository, order_id: str) -> None:
    """Accept an injected port instead of importing infrastructure."""
    repo.save(order_id)

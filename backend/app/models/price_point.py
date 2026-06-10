"""PricePoint model — time-series price records for a product."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class PricePoint(Base):
    __tablename__ = "price_points"
    __table_args__ = (
        Index("idx_price_points_product_time", "product_id", "recorded_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

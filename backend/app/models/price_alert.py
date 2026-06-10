"""PriceAlert model — records of sent / attempted price-drop notifications."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    old_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    drop_percent: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

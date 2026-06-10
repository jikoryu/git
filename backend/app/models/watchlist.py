"""WatchlistItem model — user's tracked products."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    target_price: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), nullable=True, comment="Notify when price <= this value"
    )
    notify_on_any_drop: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Notify on any price decrease"
    )
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

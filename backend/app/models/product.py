"""Product model — global product catalog keyed by platform + platform_id."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DECIMAL, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("platform", "platform_id"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="jd | taobao | pdd"
    )
    platform_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Platform-native product ID"
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    shop_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    lowest_price: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), nullable=True, comment="Historical lowest price (denormalized)"
    )
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)

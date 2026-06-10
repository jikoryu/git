"""Watchlist-related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class WatchlistCreate(BaseModel):
    product_id: str
    target_price: Decimal | None = None
    notify_on_any_drop: bool = True


class WatchlistItemOut(BaseModel):
    id: str
    product_id: str
    target_price: Decimal | None
    notify_on_any_drop: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistWithProductOut(BaseModel):
    """Watchlist item with nested product info."""
    id: str
    product_id: str
    target_price: Decimal | None
    notify_on_any_drop: bool
    created_at: datetime
    # Nested product fields
    product_title: str
    product_image: str | None
    product_url: str
    platform: str
    current_price: Decimal | None
    lowest_price: Decimal | None

    model_config = {"from_attributes": True}

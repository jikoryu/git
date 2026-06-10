"""Alert-related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class AlertOut(BaseModel):
    id: str
    product_id: str
    old_price: Decimal
    new_price: Decimal
    drop_percent: Decimal | None
    is_sent: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertWithProductOut(BaseModel):
    """Alert with nested product title / image for display."""
    id: str
    product_id: str
    old_price: Decimal
    new_price: Decimal
    drop_percent: Decimal | None
    is_sent: bool
    created_at: datetime
    product_title: str
    product_image: str | None
    platform: str

    model_config = {"from_attributes": True}

"""Product-related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class ProductOut(BaseModel):
    id: str
    platform: str
    platform_id: str
    title: str
    image_url: str | None
    shop_name: str | None
    url: str
    current_price: Decimal | None
    lowest_price: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductSearchResult(BaseModel):
    """Lightweight product card for search results."""
    id: str
    platform: str
    title: str
    image_url: str | None
    shop_name: str | None
    current_price: Decimal | None
    lowest_price: Decimal | None

    model_config = {"from_attributes": True}


class PricePointOut(BaseModel):
    price: Decimal
    recorded_at: datetime

    model_config = {"from_attributes": True}


class ProductHistoryOut(BaseModel):
    product: ProductOut
    price_history: list[PricePointOut]


class LookupRequest(BaseModel):
    url: str


class ProductSearchParams(BaseModel):
    q: str
    platform: str | None = None  # jd | taobao | pdd
    page: int = 1
    page_size: int = 20

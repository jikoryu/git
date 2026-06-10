"""Product service — search, lookup, price history."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.price_point import PricePoint


async def search_products(
    db: AsyncSession,
    keyword: str,
    platform: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[Product]:
    """Full-text search across products by title."""
    query = select(Product).where(Product.title.ilike(f"%{keyword}%"))
    if platform:
        query = query.where(Product.platform == platform)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: str) -> Product | None:
    """Get a single product by ID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def get_or_create_product(
    db: AsyncSession,
    platform: str,
    platform_id: str,
    title: str,
    url: str,
    image_url: str | None = None,
    shop_name: str | None = None,
    current_price: float | None = None,
) -> Product:
    """Find existing product or create a new one."""
    result = await db.execute(
        select(Product).where(
            Product.platform == platform,
            Product.platform_id == platform_id,
        )
    )
    product = result.scalar_one_or_none()
    if product:
        # Update mutable fields
        product.title = title
        product.url = url
        if image_url:
            product.image_url = image_url
        if shop_name:
            product.shop_name = shop_name
        if current_price is not None:
            product.current_price = current_price
            if product.lowest_price is None or current_price < product.lowest_price:
                product.lowest_price = current_price
    else:
        product = Product(
            platform=platform,
            platform_id=platform_id,
            title=title,
            url=url,
            image_url=image_url,
            shop_name=shop_name,
            current_price=current_price,
            lowest_price=current_price,
        )
        db.add(product)
    await db.flush()
    return product


async def get_price_history(
    db: AsyncSession,
    product_id: str,
    days: int = 30,
) -> list[PricePoint]:
    """Get price history for a product within the last N days."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(PricePoint)
        .where(
            PricePoint.product_id == product_id,
            PricePoint.recorded_at >= since,
        )
        .order_by(PricePoint.recorded_at.asc())
    )
    return list(result.scalars().all())


async def get_latest_price_point(
    db: AsyncSession, product_id: str
) -> PricePoint | None:
    """Get the most recent price point for a product."""
    result = await db.execute(
        select(PricePoint)
        .where(PricePoint.product_id == product_id)
        .order_by(PricePoint.recorded_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def add_price_point(
    db: AsyncSession,
    product_id: str,
    price: float,
) -> PricePoint:
    """Add a new price record. Skips duplicate if same price within 24h."""
    # Check for duplicate within last 24h
    since = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(PricePoint)
        .where(
            PricePoint.product_id == product_id,
            PricePoint.price == price,
            PricePoint.recorded_at >= since,
        )
        .limit(1)
    )
    if result.scalar_one_or_none():
        return None  # type: ignore[return-value]

    point = PricePoint(product_id=product_id, price=price)
    db.add(point)
    await db.flush()
    return point

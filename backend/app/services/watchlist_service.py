"""Watchlist service — add/remove tracked products."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.watchlist import WatchlistItem


async def get_user_watchlist(
    db: AsyncSession, user_id: str
) -> list[dict]:
    """Get all watchlist items for a user with product details."""
    result = await db.execute(
        select(WatchlistItem, Product)
        .join(Product, WatchlistItem.product_id == Product.id)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": item.id,
            "product_id": item.product_id,
            "target_price": item.target_price,
            "notify_on_any_drop": item.notify_on_any_drop,
            "created_at": item.created_at,
            "product_title": product.title,
            "product_image": product.image_url,
            "product_url": product.url,
            "platform": product.platform,
            "current_price": product.current_price,
            "lowest_price": product.lowest_price,
        }
        for item, product in rows
    ]


async def add_to_watchlist(
    db: AsyncSession,
    user_id: str,
    product_id: str,
    target_price: float | None = None,
    notify_on_any_drop: bool = True,
) -> WatchlistItem:
    """Add a product to the user's watchlist."""
    # Verify product exists
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Check for duplicate
    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.product_id == product_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already in watchlist",
        )

    item = WatchlistItem(
        user_id=user_id,
        product_id=product_id,
        target_price=target_price,
        notify_on_any_drop=notify_on_any_drop,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def remove_from_watchlist(
    db: AsyncSession,
    user_id: str,
    item_id: str,
) -> None:
    """Remove a watchlist item. Silently succeeds if not found."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.user_id == user_id,
        )
    )
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.flush()


async def get_all_active_product_ids(db: AsyncSession) -> list[str]:
    """Get distinct product IDs that are in at least one watchlist."""
    result = await db.execute(
        select(WatchlistItem.product_id).distinct()
    )
    return [row[0] for row in result.all()]

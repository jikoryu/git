"""Alert service — price-drop detection and notification triggering."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_alert import PriceAlert
from app.models.watchlist import WatchlistItem


async def check_and_create_alerts(
    db: AsyncSession,
    product_id: str,
    old_price: Decimal,
    new_price: Decimal,
) -> list[PriceAlert]:
    """Check all watchers for a product and create alerts if conditions met."""
    if new_price >= old_price:
        return []

    drop_percent = Decimal(
        round((float(old_price) - float(new_price)) / float(old_price) * 100, 2)
    )

    # Find all users watching this product
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.product_id == product_id)
    )
    watchers = result.scalars().all()

    alerts: list[PriceAlert] = []
    for w in watchers:
        should_alert = False

        if w.target_price is not None and new_price <= w.target_price:
            should_alert = True
        elif w.notify_on_any_drop and new_price < old_price:
            should_alert = True

        if should_alert:
            alert = PriceAlert(
                user_id=w.user_id,
                product_id=product_id,
                old_price=old_price,
                new_price=new_price,
                drop_percent=drop_percent,
                is_sent=False,
            )
            db.add(alert)
            alerts.append(alert)

    await db.flush()
    return alerts


async def get_user_alerts(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> list[PriceAlert]:
    """Get alert history for a user."""
    from app.models.product import Product

    result = await db.execute(
        select(PriceAlert, Product)
        .join(Product, PriceAlert.product_id == Product.id)
        .where(PriceAlert.user_id == user_id)
        .order_by(PriceAlert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.all()
    return [
        {
            "id": alert.id,
            "product_id": alert.product_id,
            "old_price": alert.old_price,
            "new_price": alert.new_price,
            "drop_percent": alert.drop_percent,
            "is_sent": alert.is_sent,
            "created_at": alert.created_at,
            "product_title": product.title,
            "product_image": product.image_url,
            "platform": product.platform,
        }
        for alert, product in rows
    ]


async def get_unsent_alerts(db: AsyncSession) -> list[PriceAlert]:
    """Get all alerts that haven't been sent yet."""
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.is_sent == False)
    )
    return list(result.scalars().all())


async def mark_alert_sent(db: AsyncSession, alert_id: str) -> None:
    """Mark an alert as sent."""
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if alert:
        alert.is_sent = True
        await db.flush()

"""Celery task for sending pending push notifications."""

import asyncio
import logging

from app.database import async_session
from app.models.product import Product
from app.services import alert_service, notification_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _send_single_alert(alert) -> bool:
    """Send a push notification for a single alert."""
    async with async_session() as db:
        # Fetch product title
        from sqlalchemy import select

        result = await db.execute(
            select(Product).where(Product.id == alert.product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            logger.warning(f"Product not found for alert {alert.id}")
            return False

        success = await notification_service.send_price_drop_notification(
            db,
            user_id=str(alert.user_id),
            product_title=product.title,
            old_price=float(alert.old_price),
            new_price=float(alert.new_price),
            drop_percent=float(alert.drop_percent) if alert.drop_percent else 0,
        )

        if success:
            await alert_service.mark_alert_sent(db, str(alert.id))

        await db.commit()
        return success


@celery_app.task(name="app.workers.tasks.notify.send_pending_notifications")
def send_pending_notifications() -> dict:
    """Scheduled task (every 5 min): send unsent price-drop push notifications."""

    async def _run():
        async with async_session() as db:
            alerts = await alert_service.get_unsent_alerts(db)

        if not alerts:
            return {"status": "ok", "sent": 0}

        sent = 0
        for alert in alerts:
            try:
                if await _send_single_alert(alert):
                    sent += 1
            except Exception as e:
                logger.error(f"Failed to send alert {alert.id}: {e}")

        logger.info(f"Sent {sent}/{len(alerts)} pending notifications")
        return {"status": "ok", "total": len(alerts), "sent": sent}

    return asyncio.get_event_loop().run_until_complete(_run())

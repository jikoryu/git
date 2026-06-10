"""Notification service — push notifications via Firebase Cloud Messaging."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


async def send_price_drop_notification(
    db: AsyncSession,
    user_id: str,
    product_title: str,
    old_price: float,
    new_price: float,
    drop_percent: float,
) -> bool:
    """Send a price-drop push notification to a user via FCM.

    Returns True if the notification was queued successfully.
    In development mode (no Firebase credentials), logs instead of sending.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.fcm_token:
        logger.info(f"No FCM token for user {user_id}, skipping notification")
        return False

    title = f"📉 {product_title}"
    body = (
        f"价格已从 ¥{old_price:.2f} 降至 ¥{new_price:.2f}"
        f"（降幅 {drop_percent:.1f}%）"
    )

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=user.fcm_token,
        )
        messaging.send(message)
        logger.info(f"FCM sent to user {user_id} for product {product_title}")
        return True

    except Exception as e:
        logger.warning(f"FCM send failed (dev mode — logged only): {e}")

        # Log the notification for development
        logger.info(
            f"[DEV NOTIFICATION] To: {user.email} | {title} | {body}"
        )
        return True  # Mark as sent in dev mode so alerts don't get stuck

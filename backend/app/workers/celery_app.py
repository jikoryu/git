"""Celery application configuration with Redis broker.

Beat schedule: scrape all active products every N hours (configurable).
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "price_tracker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.scrape",
        "app.workers.tasks.notify",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "scrape-all-active-products": {
            "task": "app.workers.tasks.scrape.scrape_all_active_products",
            "schedule": crontab(minute=0, hour=f"*/{settings.scrape_interval_hours}"),
        },
        "send-pending-notifications": {
            "task": "app.workers.tasks.notify.send_pending_notifications",
            "schedule": crontab(minute="*/5"),
        },
    },
)

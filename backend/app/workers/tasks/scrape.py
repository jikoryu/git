"""Celery tasks for product price scraping."""

import asyncio
import logging

from sqlalchemy import select

from app.database import async_session
from app.models.product import Product
from app.scrapers import SCRAPERS
from app.services import alert_service, product_service, watchlist_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _scrape_single_product(product: Product) -> dict:
    """Scrape a single product's current price and record changes."""
    scraper = SCRAPERS.get(product.platform)
    if not scraper:
        logger.warning(f"No scraper for platform: {product.platform}")
        return {"status": "skipped", "reason": "no_scraper"}

    try:
        info = await scraper.scrape(product.url)

        if info.current_price is None:
            return {"status": "skipped", "reason": "no_price_found"}

        old_price = product.current_price
        new_price = info.current_price

        async with async_session() as db:
            # Update product
            product.current_price = new_price
            if product.lowest_price is None or new_price < product.lowest_price:
                product.lowest_price = new_price

            # Record price point (deduplicated by service)
            await product_service.add_price_point(
                db, str(product.id), new_price
            )

            # Check for price drop and create alerts
            if old_price is not None and new_price < old_price:
                alerts = await alert_service.check_and_create_alerts(
                    db, str(product.id), old_price, new_price
                )
                logger.info(
                    f"Price drop for {product.title}: "
                    f"¥{old_price:.2f} → ¥{new_price:.2f} "
                    f"({len(alerts)} alerts created)"
                )
            else:
                logger.debug(
                    f"Price unchanged or increased for {product.title}: "
                    f"¥{new_price:.2f}"
                )

            await db.commit()

        return {
            "status": "ok",
            "product_id": str(product.id),
            "old_price": float(old_price) if old_price else None,
            "new_price": new_price,
        }

    except Exception as e:
        logger.error(f"Scrape failed for {product.title} ({product.url}): {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(name="app.workers.tasks.scrape.scrape_product")
def scrape_product(product_id: str) -> dict:
    """Scrape a single product by ID. Can be triggered manually or by API."""

    async def _run():
        async with async_session() as db:
            result = await db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            if not product:
                return {"status": "error", "error": "product not found"}
            return await _scrape_single_product(product)

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="app.workers.tasks.scrape.scrape_all_active_products")
def scrape_all_active_products() -> dict:
    """Scheduled task: scrape all products that are in any user's watchlist."""

    async def _run():
        async with async_session() as db:
            product_ids = await watchlist_service.get_all_active_product_ids(db)

        if not product_ids:
            logger.info("No active products to scrape")
            return {"status": "ok", "products_scraped": 0}

        results = []
        for pid in product_ids:
            async with async_session() as db:
                result = await db.execute(
                    select(Product).where(Product.id == pid)
                )
                product = result.scalar_one_or_none()
                if product:
                    r = await _scrape_single_product(product)
                    results.append(r)

        ok_count = sum(1 for r in results if r.get("status") == "ok")
        logger.info(f"Scraped {ok_count}/{len(results)} products successfully")
        return {
            "status": "ok",
            "total": len(results),
            "ok": ok_count,
            "errors": len(results) - ok_count,
        }

    return asyncio.get_event_loop().run_until_complete(_run())

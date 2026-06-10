"""Products API routes — search, detail, price history, URL lookup."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.product import (
    LookupRequest,
    ProductHistoryOut,
    ProductOut,
    PricePointOut,
)
from app.services import product_service

router = APIRouter()


@router.get("/search", response_model=list[ProductOut])
async def search_products(
    q: str = Query(..., min_length=1, description="Search keyword"),
    platform: str | None = Query(None, pattern="^(jd|taobao|pdd)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Search products by title keyword."""
    return await product_service.search_products(db, q, platform, page, page_size)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Get a single product's details."""
    product = await product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/history", response_model=ProductHistoryOut)
async def get_price_history(
    product_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Get a product's price history over a time range."""
    product = await product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    history = await product_service.get_price_history(db, product_id, days)
    return ProductHistoryOut(
        product=product,
        price_history=[PricePointOut.model_validate(p) for p in history],
    )


@router.post("/lookup", response_model=ProductOut, status_code=201)
async def lookup_product(
    data: LookupRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Look up a product by URL — scrapes the product page for current price.

    In development, returns a mock product when scraping is unavailable.
    """
    from app.scrapers import get_scraper_for_url

    scraper = get_scraper_for_url(data.url)
    if scraper is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported platform URL",
        )

    try:
        info = await scraper.scrape(data.url)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch product data from the platform",
        )

    product = await product_service.get_or_create_product(
        db,
        platform=info.platform,
        platform_id=info.platform_id,
        title=info.title,
        url=data.url,
        image_url=info.image_url,
        shop_name=info.shop_name,
        current_price=info.current_price,
    )

    # Record the first price point
    if info.current_price:
        await product_service.add_price_point(
            db, str(product.id), float(info.current_price)
        )

    await db.commit()
    await db.refresh(product)
    return product

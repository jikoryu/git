"""Watchlist API routes — CRUD for tracked products."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.watchlist import WatchlistCreate, WatchlistWithProductOut
from app.services import watchlist_service

router = APIRouter()


@router.get("/", response_model=list[WatchlistWithProductOut])
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's watchlist with product details."""
    items = await watchlist_service.get_user_watchlist(db, str(current_user.id))
    return items


@router.post("/", response_model=WatchlistWithProductOut, status_code=201)
async def add_to_watchlist(
    data: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a product to watchlist. Optionally set a target price for alerts."""
    try:
        item = await watchlist_service.add_to_watchlist(
            db,
            user_id=str(current_user.id),
            product_id=data.product_id,
            target_price=float(data.target_price) if data.target_price else None,
            notify_on_any_drop=data.notify_on_any_drop,
        )
    except HTTPException as e:
        if e.status_code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already in your watchlist",
            )
        raise

    # Fetch with product info — re-query to get joined data
    items = await watchlist_service.get_user_watchlist(db, str(current_user.id))
    created = next((i for i in items if i["id"] == str(item.id)), None)
    if created is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve created item")
    return created


@router.delete("/{item_id}", status_code=204)
async def remove_from_watchlist(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a product from watchlist."""
    await watchlist_service.remove_from_watchlist(
        db, user_id=str(current_user.id), item_id=item_id
    )

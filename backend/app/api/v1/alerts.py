"""Alerts API routes — price-drop notification history."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.alert import AlertWithProductOut
from app.services import alert_service

router = APIRouter()


@router.get("/", response_model=list[AlertWithProductOut])
async def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get price-drop alert history for the current user."""
    alerts = await alert_service.get_user_alerts(
        db, str(current_user.id), page, page_size
    )
    return alerts

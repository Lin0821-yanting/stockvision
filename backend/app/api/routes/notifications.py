"""站內通知 API（自己的提醒觸發紀錄，已讀／未讀）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.alert import AlertEventOut, NotificationsOut, ReadAllOut
from app.schemas.common import AUTH_REQUIRED_RESPONSES, ERROR_RESPONSES
from app.services import alert_service

router = APIRouter(prefix="/api/notifications", tags=["站內通知"], responses=AUTH_REQUIRED_RESPONSES)


@router.get("", response_model=NotificationsOut, summary="站內通知")
def list_notifications(
    unread_only: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationsOut:
    items, unread = alert_service.list_notifications(db, user, unread_only, limit)
    return NotificationsOut(items=[alert_service.event_out(item) for item in items], unread_count=unread)


@router.post("/read-all", response_model=ReadAllOut, summary="全部標為已讀")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReadAllOut:
    return ReadAllOut(updated=alert_service.mark_all_read(db, user))


@router.post("/{event_id}/read", response_model=AlertEventOut, summary="標為已讀")
def read_one(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AlertEventOut:
    return alert_service.event_out(alert_service.mark_read(db, user, event_id))

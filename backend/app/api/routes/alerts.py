"""價格提醒 API：建立、編輯、停用、刪除、立即檢查與觸發紀錄。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.alert import (
    AlertCheckOut,
    AlertCreate,
    AlertEventOut,
    AlertListOut,
    AlertMutationOut,
    AlertUpdate,
    MonitorStatusOut,
)
from app.schemas.common import ERROR_RESPONSES
from app.services import alert_service, catalog_service
from app.services.scheduler import monitor

router = APIRouter(prefix="/api/alerts", tags=["價格提醒"])


async def _check_one(db: Session, alert_id: int) -> AlertMutationOut:
    """建立或修改後立刻用最新價格檢查一次：條件已成立就會馬上收到通知。"""
    result = await alert_service.check_active_alerts(db, alert_ids={alert_id})
    alert = alert_service.get_alert(db, alert_id)
    return AlertMutationOut(alert=alert_service.alert_out(alert), triggered=result.events)


@router.get("", response_model=AlertListOut, summary="提醒清單與背景監控狀態")
def list_alerts(db: Session = Depends(get_db)) -> AlertListOut:
    return AlertListOut(
        alerts=[alert_service.alert_out(alert) for alert in alert_service.list_alerts(db)],
        monitor=monitor.status(),
    )


@router.post(
    "",
    response_model=AlertMutationOut,
    status_code=status.HTTP_201_CREATED,
    summary="建立價格提醒",
    responses=ERROR_RESPONSES,
)
async def create_alert(payload: AlertCreate, db: Session = Depends(get_db)) -> AlertMutationOut:
    entry = await catalog_service.resolve(db, payload.symbol)
    alert = alert_service.create_alert(db, entry, payload)
    return await _check_one(db, alert.id)


@router.patch("/{alert_id}", response_model=AlertMutationOut, summary="編輯提醒條件或啟用／停用", responses=ERROR_RESPONSES)
async def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)) -> AlertMutationOut:
    alert = alert_service.update_alert(db, alert_service.get_alert(db, alert_id), payload)
    if not alert.is_active:
        return AlertMutationOut(alert=alert_service.alert_out(alert))
    return await _check_one(db, alert.id)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除提醒（觸發紀錄會保留）", responses=ERROR_RESPONSES)
def delete_alert(alert_id: int, db: Session = Depends(get_db)) -> Response:
    alert_service.delete_alert(db, alert_service.get_alert(db, alert_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/check", response_model=AlertCheckOut, summary="立即用最新價格檢查所有啟用中的提醒")
async def check_alerts(db: Session = Depends(get_db)) -> AlertCheckOut:
    result = await alert_service.check_active_alerts(db)
    return AlertCheckOut(
        checked_alerts=result.checked_alerts,
        checked_symbols=result.checked_symbols,
        triggered=result.events,
        errors=result.errors,
        checked_at=result.checked_at,
    )


@router.get("/events", response_model=list[AlertEventOut], summary="歷史觸發紀錄")
def list_events(
    alert_id: Annotated[int | None, Query(description="只看某一個提醒")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    db: Session = Depends(get_db),
) -> list[AlertEventOut]:
    return [alert_service.event_out(event) for event in alert_service.list_events(db, alert_id, limit)]


@router.get("/monitor", response_model=MonitorStatusOut, summary="背景監控排程狀態")
def monitor_status() -> MonitorStatusOut:
    return monitor.status()

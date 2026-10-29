"""價格提醒：資料庫操作與檢查流程。

檢查時機：
1. 前端取得新行情（/api/stocks/quotes、/api/stocks/{symbol}、/api/watchlist）時同步檢查
2. 後端運行期間，APScheduler 於交易時段定期檢查（見 scheduler.py）
3. 使用者按「立即檢查」（POST /api/alerts/check）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import InvalidRequestError, NotFoundError
from app.core.market_hours import session_for
from app.models.alert import Alert, AlertEvent
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertEventOut, AlertOut, AlertUpdate
from app.schemas.stock import QuoteOut
from app.services import alert_logic, history_service, quote_service
from app.services.entities import StockEntry

KIND_LABEL = {"realtime": "盤中", "close": "收盤"}


def _currency(market: str) -> str:
    return "TWD" if market == "TW" else "USD"


def _entry(alert: Alert) -> StockEntry:
    return StockEntry(market=alert.market, symbol=alert.symbol, name=alert.name, exchange=alert.exchange)


def alert_out(alert: Alert) -> AlertOut:
    if alert.is_active:
        status, label = "monitoring", "監控中"
    elif alert.trigger_count and alert.trigger_mode == alert_logic.ONCE:
        status, label = "triggered", "已觸發（已停用）"
    else:
        status, label = "disabled", "已停用"
    return AlertOut(
        id=alert.id,
        symbol=alert.symbol,
        market=alert.market,
        name=alert.name,
        exchange=alert.exchange,
        currency=_currency(alert.market),
        condition=alert.condition,
        condition_label=alert_logic.describe(alert.condition, alert.target_price, _currency(alert.market)),
        target_price=alert.target_price,
        trigger_mode=alert.trigger_mode,
        is_active=alert.is_active,
        status=status,
        status_label=label,
        note=alert.note,
        last_condition_met=alert.last_condition_met,
        last_checked_at=alert.last_checked_at,
        last_checked_price=alert.last_checked_price,
        last_price_kind=alert.last_price_kind,
        last_triggered_at=alert.last_triggered_at,
        trigger_count=alert.trigger_count,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def event_out(event: AlertEvent) -> AlertEventOut:
    return AlertEventOut(
        id=event.id,
        alert_id=event.alert_id,
        symbol=event.symbol,
        market=event.market,
        name=event.name,
        condition=event.condition,
        condition_label=alert_logic.describe(event.condition, event.target_price, _currency(event.market)),
        target_price=event.target_price,
        triggered_price=event.triggered_price,
        reference_low=event.reference_low,
        price_kind=event.price_kind,
        price_source=event.price_source,
        price_as_of=event.price_as_of,
        message=event.message,
        triggered_at=event.triggered_at,
        read_at=event.read_at,
    )


def _message(alert: Alert, quote: QuoteOut, low_20d: Decimal | None) -> str:
    currency = _currency(alert.market)
    session = session_for(alert.market)
    when = quote.as_of.astimezone(session.timezone).strftime("%m/%d %H:%M") if quote.as_of else "—"
    if alert.condition == alert_logic.NEW_20D_LOW:
        reason = f"創 20 日新低（前 20 日最低收盤 {low_20d:,.2f}）"
    else:
        reason = alert_logic.describe(alert.condition, alert.target_price, currency)
    return (
        f"{alert.name}（{alert.symbol}）{reason}：最新價格 {quote.price:,.2f} {currency}"
        f"（{KIND_LABEL[quote.kind]}・{quote.source}・{when} {session.timezone_label}）"
    )


# ---------------------------------------------------------------- CRUD


def list_alerts(db: Session, user: User) -> list[Alert]:
    return list(
        db.scalars(
            select(Alert)
            .where(Alert.user_id == user.id)
            .order_by(Alert.is_active.desc(), Alert.created_at.desc(), Alert.id.desc())
        )
    )


def get_alert(db: Session, user: User, alert_id: int) -> Alert:
    """別人的提醒一律當作不存在（404），不透露編號是否存在。"""
    alert = db.get(Alert, alert_id)
    if alert is None or alert.user_id != user.id:
        raise NotFoundError(f"找不到編號 {alert_id} 的提醒", details={"alert_id": alert_id})
    return alert


def create_alert(db: Session, user: User, entry: StockEntry, payload: AlertCreate) -> Alert:
    now = clock.now()
    alert = Alert(
        user_id=user.id,
        market=entry.market,
        symbol=entry.symbol,
        name=entry.name,
        exchange=entry.exchange,
        condition=payload.condition,
        target_price=payload.target_price,
        trigger_mode=payload.trigger_mode,
        is_active=True,
        note=payload.note,
        created_at=now,
        updated_at=now,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def update_alert(db: Session, alert: Alert, payload: AlertUpdate) -> Alert:
    changes = payload.model_dump(exclude_unset=True)
    condition = changes.get("condition", alert.condition)
    target = changes.get("target_price", alert.target_price)
    if condition == alert_logic.NEW_20D_LOW:
        target = None
    elif target is None:
        raise InvalidRequestError("價格條件需要設定目標價格")

    rearm = (
        condition != alert.condition
        or target != alert.target_price
        or (changes.get("is_active") is True and not alert.is_active)
    )
    alert.condition = condition
    alert.target_price = target
    if "trigger_mode" in changes:
        alert.trigger_mode = changes["trigger_mode"]
    if "is_active" in changes:
        alert.is_active = changes["is_active"]
    if "note" in changes:
        alert.note = changes["note"]
    if rearm:
        # 條件改變或重新啟用後重新開始判斷，若條件已成立會立即通知
        alert.last_condition_met = False
    alert.updated_at = clock.now()
    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert: Alert) -> None:
    db.execute(update(AlertEvent).where(AlertEvent.alert_id == alert.id).values(alert_id=None))
    db.delete(alert)
    db.commit()


# ---------------------------------------------------------------- 檢查


async def process_quotes(db: Session, quotes: list[QuoteOut], user: User | None) -> list[AlertEventOut]:
    """用剛取得的報價檢查「所有使用者」的相關提醒，但只回傳目前使用者自己的新通知。"""
    events = await evaluate_quotes(db, quotes)
    if user is None:
        return []
    return [event_out(event) for event in events if event.user_id == user.id]


async def evaluate_quotes(db: Session, quotes: list[QuoteOut]) -> list[AlertEvent]:
    """伺服器端持續監控：任何人取得行情、或背景排程執行時，都會檢查這些股票的所有啟用中提醒。"""
    priced = {(quote.market, quote.symbol): quote for quote in quotes if quote.price is not None}
    if not priced:
        return []
    symbols = {symbol for _, symbol in priced}
    alerts = [
        alert
        for alert in db.scalars(select(Alert).where(Alert.is_active.is_(True), Alert.symbol.in_(symbols)))
        if (alert.market, alert.symbol) in priced
    ]
    if not alerts:
        return []

    lows: dict[tuple[str, str], Decimal | None] = {}
    for alert in alerts:
        key = (alert.market, alert.symbol)
        if alert.condition == alert_logic.NEW_20D_LOW and key not in lows:
            lows[key], _ = await history_service.twenty_day_low(_entry(alert), priced[key])

    now = clock.now()
    events: list[AlertEvent] = []
    for alert in alerts:
        key = (alert.market, alert.symbol)
        quote = priced[key]
        result = alert_logic.evaluate(
            condition=alert.condition,
            target=alert.target_price,
            trigger_mode=alert.trigger_mode,
            previously_met=alert.last_condition_met,
            price=quote.price,
            low_20d=lows.get(key),
        )
        alert.last_checked_at = now
        alert.last_checked_price = quote.price
        alert.last_price_kind = quote.kind
        alert.last_condition_met = result.condition_met
        if result.triggered:
            event = AlertEvent(
                user_id=alert.user_id,
                alert_id=alert.id,
                market=alert.market,
                symbol=alert.symbol,
                name=alert.name,
                condition=alert.condition,
                target_price=alert.target_price,
                triggered_price=quote.price,
                reference_low=lows.get(key),
                price_kind=quote.kind,
                price_source=quote.source,
                price_as_of=quote.as_of,
                message=_message(alert, quote, lows.get(key)),
                triggered_at=now,
            )
            db.add(event)
            events.append(event)
            alert.trigger_count += 1
            alert.last_triggered_at = now
        if result.deactivate:
            alert.is_active = False
    db.commit()
    for event in events:
        db.refresh(event)
    return events


@dataclass
class CheckResult:
    checked_alerts: int
    checked_symbols: int
    events: list[AlertEventOut] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    checked_at: datetime | None = None


async def check_active_alerts(
    db: Session,
    markets: set[str] | None = None,
    alert_ids: set[int] | None = None,
    user: User | None = None,
) -> CheckResult:
    """抓取啟用中提醒的最新報價並檢查。

    排程呼叫時 user 為 None，檢查所有人的提醒；markets 讓排程只檢查開盤中的市場。
    使用者按「立即檢查」時只檢查、也只回傳自己的提醒。
    """
    statement = select(Alert).where(Alert.is_active.is_(True))
    if user is not None:
        statement = statement.where(Alert.user_id == user.id)
    alerts = [
        alert
        for alert in db.scalars(statement)
        if (markets is None or alert.market in markets) and (alert_ids is None or alert.id in alert_ids)
    ]
    entries = list({_entry(alert).key: _entry(alert) for alert in alerts}.values())
    result = CheckResult(checked_alerts=len(alerts), checked_symbols=len(entries), checked_at=clock.now())
    if not entries:
        return result
    quote_results = await quote_service.get_quotes(entries)
    result.errors = [f"{r.entry.symbol}：{r.error.message}" for r in quote_results if r.quote is None and r.error]
    events = await evaluate_quotes(db, [r.quote for r in quote_results if r.quote is not None])
    result.events = [event_out(event) for event in events if user is None or event.user_id == user.id]
    return result


# ---------------------------------------------------------------- 站內通知


def list_notifications(db: Session, user: User, unread_only: bool, limit: int) -> tuple[list[AlertEvent], int]:
    statement = select(AlertEvent).where(AlertEvent.user_id == user.id)
    if unread_only:
        statement = statement.where(AlertEvent.read_at.is_(None))
    items = list(db.scalars(statement.order_by(AlertEvent.triggered_at.desc(), AlertEvent.id.desc()).limit(limit)))
    unread = (
        db.scalar(
            select(func.count())
            .select_from(AlertEvent)
            .where(AlertEvent.user_id == user.id, AlertEvent.read_at.is_(None))
        )
        or 0
    )
    return items, unread


def list_events(db: Session, user: User, alert_id: int | None, limit: int) -> list[AlertEvent]:
    statement = select(AlertEvent).where(AlertEvent.user_id == user.id)
    if alert_id is not None:
        statement = statement.where(AlertEvent.alert_id == alert_id)
    return list(db.scalars(statement.order_by(AlertEvent.triggered_at.desc(), AlertEvent.id.desc()).limit(limit)))


def mark_read(db: Session, user: User, event_id: int) -> AlertEvent:
    event = db.get(AlertEvent, event_id)
    if event is None or event.user_id != user.id:
        raise NotFoundError(f"找不到編號 {event_id} 的通知", details={"event_id": event_id})
    if event.read_at is None:
        event.read_at = clock.now()
        db.commit()
        db.refresh(event)
    return event


def mark_all_read(db: Session, user: User) -> int:
    result = db.execute(
        update(AlertEvent)
        .where(AlertEvent.user_id == user.id, AlertEvent.read_at.is_(None))
        .values(read_at=clock.now())
    )
    db.commit()
    return result.rowcount or 0

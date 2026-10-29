"""APScheduler 背景排程：後端運行期間，於交易時段定期檢查啟用中的價格提醒。

- 只在台股或美股開盤時才真的抓報價（休市時跳過，不浪費 API 額度）
- max_instances=1、coalesce=True：上一輪還沒跑完不會疊加執行
- 只有後端服務在執行時才會監控；網站與後端都關閉時無法監控價格
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core import clock
from app.core.config import get_settings
from app.core.market_hours import SESSIONS, TAIPEI
from app.database.session import SessionLocal
from app.schemas.alert import MonitorStatusOut
from app.services import alert_service

logger = logging.getLogger("stockvision.scheduler")

EXPLANATION = (
    "提醒由 Python 後端判斷：前端取得新行情時會同步檢查；後端運行期間，背景排程也會在交易時段定期檢查。"
    "若網站與後端服務都已關閉，系統無法監控價格。目前沒有手機推播、LINE 或 Email 通知，只有站內通知。"
)


class AlertMonitor:
    JOB_ID = "alert-check"

    def __init__(self) -> None:
        self.scheduler: AsyncIOScheduler | None = None
        self.last_run_at: datetime | None = None
        self.last_result = "尚未執行"

    def start(self) -> None:
        settings = get_settings()
        if not settings.alert_scheduler_enabled:
            self.last_result = "背景排程已停用（ALERT_SCHEDULER_ENABLED=false）"
            return
        self.scheduler = AsyncIOScheduler(timezone=TAIPEI)
        self.scheduler.add_job(
            self.run_once,
            "interval",
            seconds=settings.alert_check_interval_seconds,
            id=self.JOB_ID,
            max_instances=1,
            coalesce=True,
            next_run_time=datetime.now(TAIPEI) + timedelta(seconds=15),
        )
        self.scheduler.start()
        logger.info("Alert monitor started (every %ss)", settings.alert_check_interval_seconds)

    def shutdown(self) -> None:
        if self.scheduler is not None and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.scheduler = None

    @staticmethod
    def open_markets() -> set[str]:
        now = clock.now()
        return {market for market, session in SESSIONS.items() if session.is_open(now)}

    async def run_once(self) -> None:
        self.last_run_at = clock.now()
        markets = self.open_markets()
        if not markets:
            self.last_result = "台股與美股都不在交易時段，略過檢查"
            return
        with SessionLocal() as db:
            try:
                result = await alert_service.check_active_alerts(db, markets=markets)
            except Exception as exc:  # 排程不能因為一次失敗就停止
                logger.exception("Scheduled alert check failed")
                self.last_result = f"檢查失敗：{exc}"
                return
        self.last_result = f"檢查 {result.checked_alerts} 個提醒（{result.checked_symbols} 檔股票），觸發 {len(result.events)} 個"
        if result.errors:
            self.last_result += f"；{len(result.errors)} 檔取價失敗"

    def status(self) -> MonitorStatusOut:
        settings = get_settings()
        job = self.scheduler.get_job(self.JOB_ID) if self.scheduler else None
        return MonitorStatusOut(
            enabled=settings.alert_scheduler_enabled,
            interval_seconds=settings.alert_check_interval_seconds,
            running=bool(self.scheduler and self.scheduler.running),
            last_run_at=self.last_run_at,
            last_result=self.last_result,
            next_run_at=job.next_run_time if job else None,
            markets_open=sorted(self.open_markets()),
            explanation=EXPLANATION,
        )


monitor = AlertMonitor()

"""台股與美股的交易時段判斷。

只依星期與時間判斷，沒有內建國定假日行事曆；假日時報價會停在最後交易日，
前端會以報價時間顯示，不會把舊資料標成盤中。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.core import clock

TAIPEI = ZoneInfo("Asia/Taipei")
NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class MarketSession:
    market: str
    name: str
    timezone: ZoneInfo
    timezone_label: str
    open_time: time
    close_time: time

    def local_now(self, now: datetime | None = None) -> datetime:
        return (now or clock.now()).astimezone(self.timezone)

    def today(self, now: datetime | None = None) -> date:
        return self.local_now(now).date()

    def is_open(self, now: datetime | None = None) -> bool:
        return self.state(now)[0] == "open"

    def state(self, now: datetime | None = None) -> tuple[str, str]:
        local = self.local_now(now)
        if local.weekday() >= 5:
            return "closed", "休市（週末）"
        if local.time() < self.open_time:
            return "pre_open", "尚未開盤"
        if local.time() < self.close_time:
            return "open", "盤中"
        return "closed", "已收盤"

    def close_datetime(self, day: date) -> datetime:
        return datetime.combine(day, self.close_time, tzinfo=self.timezone)

    def session_in_taipei(self, now: datetime | None = None) -> str:
        """交易時段換算成台北時間（美股會隨夏令時間變動）。"""
        day = self.today(now)
        start = datetime.combine(day, self.open_time, tzinfo=self.timezone).astimezone(TAIPEI)
        end = datetime.combine(day, self.close_time, tzinfo=self.timezone).astimezone(TAIPEI)
        return f"{start:%H:%M}–{end:%H:%M}"


SESSIONS: dict[str, MarketSession] = {
    "TW": MarketSession("TW", "台股", TAIPEI, "台北時間", time(9, 0), time(13, 30)),
    "US": MarketSession("US", "美股", NEW_YORK, "紐約時間", time(9, 30), time(16, 0)),
}


def session_for(market: str) -> MarketSession:
    return SESSIONS[market]

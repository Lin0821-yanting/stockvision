"""臺灣證券交易所 OpenAPI（https://openapi.twse.com.tw/）：上市個股最新一日成交資訊與上市公司基本資料。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.core.money import to_decimal
from app.services.providers.base import DailySnapshot, parse_roc_date
from app.services.providers.http import get_json

STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
SOURCE = "TWSE OpenAPI STOCK_DAY_ALL"
COMPANY_BASICS_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
COMPANY_SOURCE = "TWSE OpenAPI t187ap03_L"


@dataclass(frozen=True)
class CompanyBasics:
    """上市公司基本資料（只保留計算市值需要的欄位）。"""

    symbol: str
    short_name: str
    shares: int  # 已發行普通股數；TDR 為原股發行股數
    report_date: date | None


def parse_stock_day_all(payload: Any) -> dict[str, DailySnapshot]:
    snapshots: dict[str, DailySnapshot] = {}
    for row in payload if isinstance(payload, list) else []:
        code = str(row.get("Code", "")).strip()
        trade_date = parse_roc_date(row.get("Date", ""))
        if not code or trade_date is None:
            continue
        volume = to_decimal(row.get("TradeVolume"))
        snapshots[code] = DailySnapshot(
            symbol=code,
            name=str(row.get("Name", "")).strip(),
            trade_date=trade_date,
            open=to_decimal(row.get("OpeningPrice")),
            high=to_decimal(row.get("HighestPrice")),
            low=to_decimal(row.get("LowestPrice")),
            close=to_decimal(row.get("ClosingPrice")),
            change=to_decimal(row.get("Change")),
            volume=int(volume) if volume is not None else None,
            source=SOURCE,
        )
    return snapshots


async def fetch_stock_day_all() -> dict[str, DailySnapshot]:
    return parse_stock_day_all(await get_json(STOCK_DAY_ALL_URL, source=SOURCE))


def parse_company_basics(payload: Any) -> list[CompanyBasics]:
    companies: list[CompanyBasics] = []
    for row in payload if isinstance(payload, list) else []:
        code = str(row.get("公司代號", "")).strip()
        shares = to_decimal(row.get("已發行普通股數或TDR原股發行股數"))
        if not code or shares is None or shares <= 0:
            continue
        companies.append(
            CompanyBasics(
                symbol=code,
                short_name=str(row.get("公司簡稱", "")).strip() or code,
                shares=int(shares),
                report_date=parse_roc_date(row.get("出表日期", "")),
            )
        )
    return companies


async def fetch_company_basics() -> list[CompanyBasics]:
    return parse_company_basics(await get_json(COMPANY_BASICS_URL, source=COMPANY_SOURCE))

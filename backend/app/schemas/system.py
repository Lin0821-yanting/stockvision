"""系統狀態相關的回應結構。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DataSourceStatus(BaseModel):
    name: str
    purpose: str
    configured: bool
    note: str


class HealthOut(BaseModel):
    status: str
    app: str
    version: str
    server_time: datetime
    data_sources: list[DataSourceStatus]

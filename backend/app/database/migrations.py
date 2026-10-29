"""SQLite 結構遷移（可重複執行）。

第一版是單人模式；加入登入後，帳戶、自選股、提醒與通知都要歸屬到使用者。
`create_all` 不會修改既有的資料表，所以要在它之前補上新欄位、重建自選股表並建立索引。
`user_id` 為空的舊資料會在第一位使用者註冊時交給他（見 auth_service.claim_legacy_data）。
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.engine import Connection, Engine

from app.models.user import User, UserSession
from app.models.watchlist import WatchlistItem

logger = logging.getLogger("stockvision.migrations")

USER_COLUMN = "INTEGER REFERENCES users(id) ON DELETE CASCADE"
USER_INDEXES = {
    "accounts": "CREATE UNIQUE INDEX IF NOT EXISTS uq_accounts_user ON accounts (user_id)",
    "alerts": "CREATE INDEX IF NOT EXISTS ix_alerts_user_id ON alerts (user_id)",
    "alert_events": "CREATE INDEX IF NOT EXISTS ix_alert_events_user_id ON alert_events (user_id)",
}


def _tables(conn: Connection) -> set[str]:
    return set(inspect(conn).get_table_names())


def _columns(conn: Connection, table: str) -> set[str]:
    return {column["name"] for column in inspect(conn).get_columns(table)}


def ensure_column(conn: Connection, table: str, column: str, ddl: str) -> bool:
    if column in _columns(conn, table):
        return False
    conn.exec_driver_sql(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {ddl}')
    return True


def _rebuild_watchlist(conn: Connection) -> None:
    """舊表的唯一鍵是 (market, symbol)；SQLite 不能修改限制，只能換成新表再搬資料。"""
    conn.exec_driver_sql("ALTER TABLE watchlist_items RENAME TO watchlist_items_legacy")
    WatchlistItem.__table__.create(conn)
    conn.exec_driver_sql(
        "INSERT INTO watchlist_items (id, user_id, market, symbol, name, exchange, created_at) "
        "SELECT id, NULL, market, symbol, name, exchange, created_at FROM watchlist_items_legacy"
    )
    conn.exec_driver_sql("DROP TABLE watchlist_items_legacy")


def needs_upgrade(engine: Engine) -> bool:
    """既有資料庫是不是單人模式的舊結構。"""
    with engine.connect() as conn:
        return "accounts" in _tables(conn) and "user_id" not in _columns(conn, "accounts")


def backup_sqlite(database_url: str) -> Path | None:
    """用 SQLite backup API 備份（含 WAL 中尚未寫回主檔的資料）。"""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix) or ":memory:" in database_url:
        return None
    path = Path(database_url[len(prefix):])
    if not path.exists():
        return None
    target = path.with_name(f"{path.stem}.backup-{datetime.now():%Y%m%d-%H%M%S}{path.suffix}")
    source = sqlite3.connect(path)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    return target


def migrate(engine: Engine) -> list[str]:
    """把舊結構升級成目前的結構，回傳做過的步驟；全新的資料庫交給 create_all。"""
    steps: list[str] = []
    with engine.begin() as conn:
        tables = _tables(conn)
        if not tables:
            return steps
        User.__table__.create(conn, checkfirst=True)
        UserSession.__table__.create(conn, checkfirst=True)
        for table, index_sql in USER_INDEXES.items():
            if table not in tables:
                continue
            if ensure_column(conn, table, "user_id", USER_COLUMN):
                steps.append(f"{table}.user_id")
            conn.exec_driver_sql(index_sql)
        if "watchlist_items" in tables and "user_id" not in _columns(conn, "watchlist_items"):
            _rebuild_watchlist(conn)
            steps.append("watchlist_items rebuilt")
    if steps:
        logger.warning("Database schema upgraded: %s", ", ".join(steps))
    return steps

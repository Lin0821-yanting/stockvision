"""SQLAlchemy engine、Session 與資料庫初始化。"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

logger = logging.getLogger("stockvision.database")


class Base(DeclarativeBase):
    pass


def _is_memory_sqlite(url: str) -> bool:
    return url.startswith("sqlite") and (":memory:" in url or url.rstrip("/").endswith(":"))


def build_engine(url: str) -> Engine:
    kwargs: dict = {}
    is_sqlite = url.startswith("sqlite")
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
        if _is_memory_sqlite(url):
            # 記憶體資料庫（測試用）要共用同一條連線，否則每個 Session 都會看到空的資料庫
            kwargs["poolclass"] = StaticPool
        else:
            Path(url.split("///", 1)[-1]).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, **kwargs)

    if is_sqlite:
        use_wal = not _is_memory_sqlite(url)

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            if use_wal:
                # WAL 讓背景排程寫入時，前端請求仍可同時讀取
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


engine = build_engine(get_settings().resolved_database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """升級舊結構（必要時先備份）並建立所有資料表；重複執行是安全的。"""
    from app import models  # noqa: F401  匯入後所有 model 才會註冊到 Base.metadata
    from app.database import migrations

    if migrations.needs_upgrade(engine):
        backup = migrations.backup_sqlite(get_settings().resolved_database_url)
        logger.warning("Upgrading single-user database for login support; backup saved to %s", backup)
    migrations.migrate(engine)
    Base.metadata.create_all(bind=engine)

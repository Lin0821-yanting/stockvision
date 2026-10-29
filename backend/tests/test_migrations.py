"""單人模式資料庫升級：補欄位、重建自選股表、備份，以及第一位註冊者接收舊資料。"""

import sqlite3
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import migrations
from app.database.session import Base, build_engine
from app.models.account import Account
from app.models.alert import Alert, AlertEvent
from app.models.watchlist import WatchlistItem
from app.services import auth_service

# 第一版（沒有登入）的資料表結構，只列出這次遷移會動到的欄位
LEGACY_SQL = """
CREATE TABLE accounts (
    id INTEGER NOT NULL PRIMARY KEY, base_currency VARCHAR(3) NOT NULL, initial_cash VARCHAR(64) NOT NULL,
    cash VARCHAR(64) NOT NULL, cycle INTEGER NOT NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
    reset_at DATETIME
);
CREATE TABLE watchlist_items (
    id INTEGER NOT NULL PRIMARY KEY, market VARCHAR(4) NOT NULL, symbol VARCHAR(16) NOT NULL,
    name VARCHAR(200) NOT NULL, exchange VARCHAR(16) NOT NULL, created_at DATETIME NOT NULL,
    CONSTRAINT uq_watchlist_market_symbol UNIQUE (market, symbol)
);
CREATE TABLE alerts (
    id INTEGER NOT NULL PRIMARY KEY, market VARCHAR(4) NOT NULL, symbol VARCHAR(16) NOT NULL, name VARCHAR(200) NOT NULL,
    exchange VARCHAR(16) NOT NULL, condition VARCHAR(16) NOT NULL, target_price VARCHAR(64), trigger_mode VARCHAR(12) NOT NULL,
    is_active BOOLEAN NOT NULL, note VARCHAR(200), last_condition_met BOOLEAN NOT NULL, last_checked_at DATETIME,
    last_checked_price VARCHAR(64), last_price_kind VARCHAR(10), last_triggered_at DATETIME, trigger_count INTEGER NOT NULL,
    created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
);
CREATE TABLE alert_events (
    id INTEGER NOT NULL PRIMARY KEY, alert_id INTEGER REFERENCES alerts (id) ON DELETE SET NULL, market VARCHAR(4) NOT NULL,
    symbol VARCHAR(16) NOT NULL, name VARCHAR(200) NOT NULL, condition VARCHAR(16) NOT NULL, target_price VARCHAR(64),
    triggered_price VARCHAR(64) NOT NULL, reference_low VARCHAR(64), price_kind VARCHAR(10) NOT NULL,
    price_source VARCHAR(80) NOT NULL, price_as_of DATETIME, message VARCHAR(400) NOT NULL, triggered_at DATETIME NOT NULL,
    read_at DATETIME
);
INSERT INTO accounts VALUES (1, 'TWD', '1000000', '758500.00', 1, '2026-10-29 01:00:00', '2026-10-29 01:00:00', NULL);
INSERT INTO watchlist_items VALUES (1, 'TW', '2330', '台積電', 'TWSE', '2026-10-29 01:00:00');
INSERT INTO watchlist_items VALUES (2, 'US', 'AAPL', 'Apple Inc.', 'US', '2026-10-29 01:00:00');
INSERT INTO alerts VALUES (1, 'TW', '2330', '台積電', 'TWSE', 'PRICE_LTE', '900', 'ONCE', 1, NULL, 0, NULL, NULL, NULL, NULL, 0,
    '2026-10-29 01:00:00', '2026-10-29 01:00:00');
INSERT INTO alert_events VALUES (1, 1, 'TW', '2330', '台積電', 'PRICE_LTE', '900', '880', NULL, 'close', 'TWSE MIS', NULL,
    '舊通知', '2026-10-29 01:00:00', NULL);
"""


def legacy_engine(tmp_path):
    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript(LEGACY_SQL)
    connection.close()
    return build_engine(f"sqlite:///{path.as_posix()}"), path


def upgrade(engine) -> list[str]:
    steps = migrations.migrate(engine)
    Base.metadata.create_all(bind=engine)
    return steps


def test_legacy_schema_is_upgraded_and_rerun_is_safe(tmp_path):
    engine, _ = legacy_engine(tmp_path)
    assert migrations.needs_upgrade(engine)

    steps = upgrade(engine)

    assert {"accounts.user_id", "alerts.user_id", "alert_events.user_id", "watchlist_items rebuilt"} <= set(steps)
    assert not migrations.needs_upgrade(engine)
    assert upgrade(engine) == []  # 再跑一次不會重複修改
    with Session(engine) as db:
        assert db.query(WatchlistItem).count() == 2
        assert db.query(Alert).count() == 1


def test_first_user_claims_legacy_data_and_later_users_start_fresh(tmp_path):
    engine, _ = legacy_engine(tmp_path)
    upgrade(engine)

    with Session(engine, expire_on_commit=False) as db:
        alice = auth_service.register(db, "alice", "password-123", None)
        bob = auth_service.register(db, "bob", "password-123", None)

        alice_account = db.scalar(select(Account).where(Account.user_id == alice.id))
        bob_account = db.scalar(select(Account).where(Account.user_id == bob.id))
        assert alice_account.id == 1 and alice_account.cash == Decimal("758500.00")  # 原本的帳戶與現金
        assert bob_account.cash == Decimal("1000000")
        assert db.query(WatchlistItem).filter_by(user_id=alice.id).count() == 2
        assert db.query(Alert).filter_by(user_id=alice.id).count() == 1
        assert db.query(AlertEvent).filter_by(user_id=alice.id).count() == 1

        db.add(WatchlistItem(user_id=bob.id, market="TW", symbol="2330", name="台積電", exchange="TWSE"))
        db.commit()  # 新的唯一鍵含 user_id，不同使用者可以加入同一檔股票
        assert db.query(WatchlistItem).filter_by(symbol="2330").count() == 2


def test_backup_copies_the_database(tmp_path):
    engine, path = legacy_engine(tmp_path)
    engine.dispose()

    backup = migrations.backup_sqlite(f"sqlite:///{path.as_posix()}")

    assert backup is not None and backup.exists()
    copied = sqlite3.connect(backup)
    assert copied.execute("SELECT cash FROM accounts").fetchone() == ("758500.00",)
    copied.close()
    assert migrations.backup_sqlite("sqlite:///:memory:") is None

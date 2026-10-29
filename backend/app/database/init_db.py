"""手動初始化 SQLite 資料庫：

    python -m app.database.init_db

後端啟動時也會自動執行相同的初始化，這個指令方便第一次安裝時確認資料庫位置。
"""

from __future__ import annotations

from app.core.config import get_settings
from app.database.session import init_db


def main() -> None:
    init_db()
    print(f"資料庫已初始化：{get_settings().resolved_database_url}")


if __name__ == "__main__":
    main()

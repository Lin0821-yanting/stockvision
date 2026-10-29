"""所有 ORM model。init_db() 匯入這個套件，確保資料表都會被建立。"""

from app.models.catalog import StockCatalog

__all__ = ["StockCatalog"]

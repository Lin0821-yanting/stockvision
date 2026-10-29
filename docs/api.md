# StockVision API

- Base URL：`http://localhost:8000`
- 互動式文件：Swagger UI `http://localhost:8000/docs`、ReDoc `http://localhost:8000/redoc`
- 金額以 JSON 數字回傳（後端以 `Decimal` 計算與儲存）；時間為 ISO 8601（含時區）

## 錯誤格式

```json
{
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "可用資金不足：需要 NT$ 2,415,000.00，目前可用 NT$ 1,000,000.00",
    "details": { "required": "2415000.00", "available": "1000000" }
  }
}
```

| HTTP | code | 情境 |
|---|---|---|
| 400 | `INVALID_REQUEST` | 參數不合理，例如比較少於 2 檔 |
| 400 | `INSUFFICIENT_FUNDS` / `INSUFFICIENT_SHARES` | 資金不足、持股不足 |
| 404 | `SYMBOL_NOT_FOUND` / `NOT_FOUND` | 找不到股票代號、提醒或通知 |
| 409 | `CONFLICT` | 自選股重複 |
| 422 | `VALIDATION_ERROR` | 欄位格式錯誤（例如 period 不是 1M/3M/6M/1Y） |
| 503 | `UPSTREAM_UNAVAILABLE` / `UPSTREAM_RATE_LIMITED` / `MARKET_PRICE_UNAVAILABLE` | 外部股票 API 失敗、額度用完、暫時沒有價格 |

## 系統與市況

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/health` | 健康檢查、資料來源設定狀態、背景排程狀態 |
| GET | `/api/market/status` | 台股、美股是否在交易時段（含換算成台北時間的美股時段） |
| GET | `/api/fx/usd-twd` | USD/TWD 匯率（臺灣銀行即期中價） |

## 股票資料

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/stocks/search?q=台積&market=TW&limit=20` | 搜尋代號或名稱（本機股票清單） |
| GET | `/api/stocks/quotes?symbols=2330,2317,AAPL` | 批次最新報價（最多 30 檔），並同步檢查提醒 |
| GET | `/api/stocks/compare?symbols=2330,2317&period=3M` | 2–4 檔標準化比較（Pandas） |
| GET | `/api/stocks/{symbol}` | 個股資訊、最新報價、20 日最低收盤、是否創 20 日新低 |
| GET | `/api/stocks/{symbol}/history?period=1M` | 歷史日資料（1M/3M/6M/1Y）與區間統計 |

`GET /api/stocks/2330` 回應範例（收盤後）：

```json
{
  "stock": { "symbol": "2330", "market": "TW", "name": "台積電", "exchange": "TWSE", "currency": "TWD" },
  "quote": {
    "price": 2415.0, "change": -10.0, "change_pct": -0.4124,
    "open": 2420.0, "high": 2425.0, "low": 2390.0, "prev_close": 2425.0,
    "volume": 16828000, "trade_date": "2026-10-29", "as_of": "2026-10-29T13:30:00+08:00",
    "kind": "close", "source": "TWSE MIS", "note": "今日收盤（TWSE MIS）",
    "market_open": false, "fetched_at": "2026-10-29T10:42:27Z"
  },
  "low_20d": 2385.0,
  "is_20d_low": false,
  "triggered_alerts": []
}
```

## 自選股

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/watchlist?with_quotes=true` | 自選股（附最新報價） |
| POST | `/api/watchlist` | body `{"symbol": "2330"}`，重複時回 409 |
| DELETE | `/api/watchlist/{symbol}` | 移除（204） |

## 模擬交易

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/account` | 現金、初始資金、回合 |
| POST | `/api/account/reset` | 重置：清空持股、現金回到 NT$1,000,000、交易紀錄保留 |
| GET | `/api/portfolio` | 持股市值、未實現／已實現損益、總資產、報酬率、配置比例 |
| POST | `/api/trades/preview` | 試算（不成交），body `{"symbol":"2330","side":"BUY","shares":100}` |
| POST | `/api/trades` | 模擬成交（價格由後端取得），201 |
| GET | `/api/trades?scope=current&limit=100` | 交易紀錄；`scope=all` 包含重置前 |

## 價格提醒與通知

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/alerts` | 提醒清單＋背景排程狀態 |
| POST | `/api/alerts` | body `{"symbol":"2330","condition":"PRICE_LTE","target_price":900,"trigger_mode":"ONCE"}`；建立後立即檢查 |
| PATCH | `/api/alerts/{id}` | 修改條件、目標價、模式、啟用／停用（修改後重新檢查） |
| DELETE | `/api/alerts/{id}` | 刪除（觸發紀錄保留） |
| POST | `/api/alerts/check` | 立即檢查所有啟用中的提醒 |
| GET | `/api/alerts/events?alert_id=&limit=100` | 歷史觸發紀錄 |
| GET | `/api/alerts/monitor` | 背景排程狀態與執行條件說明 |
| GET | `/api/notifications?unread_only=false` | 站內通知與未讀數 |
| POST | `/api/notifications/{id}/read` | 標為已讀 |
| POST | `/api/notifications/read-all` | 全部標為已讀 |

`condition`：`PRICE_LTE`（價格 ≤ 目標價）、`PRICE_GTE`（價格 ≥ 目標價）、`NEW_20D_LOW`（創 20 日新低，不需目標價）。
`trigger_mode`：`ONCE`（觸發後停用）、`EVERY_CROSS`（每次由不成立變成立都通知）。

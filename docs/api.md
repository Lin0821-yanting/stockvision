# StockVision API

- Base URL：`http://localhost:8000`
- 互動式文件：Swagger UI `http://localhost:8000/docs`、ReDoc `http://localhost:8000/redoc`
- 金額以 JSON 數字回傳（後端以 `Decimal` 計算與儲存）；時間為 ISO 8601（含時區）
- 🔒 表示需要登入：瀏覽器會自動帶著 HttpOnly cookie `sv_session`；API 工具可以改用 `Authorization: Bearer <token>`。未登入回 401 `AUTH_REQUIRED`
- 在 Swagger 測試 🔒 端點：先執行 `POST /api/auth/register` 或 `POST /api/auth/login`，之後同一個頁面的 Try it out 就是登入狀態

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
| 401 | `AUTH_REQUIRED` | 尚未登入、session 過期或已登出 |
| 401 | `INVALID_CREDENTIALS` | 帳號或密碼錯誤（不透露是哪一項錯） |
| 403 | `REGISTRATION_DISABLED` | `REGISTRATION_ENABLED=false` 時註冊 |
| 404 | `SYMBOL_NOT_FOUND` / `NOT_FOUND` | 找不到股票代號、提醒或通知（包含別人的提醒） |
| 409 | `CONFLICT` | 自選股重複、帳號已經有人使用 |
| 422 | `VALIDATION_ERROR` | 欄位格式錯誤（例如 period 不是 1M/3M/6M/1Y、帳號格式不符） |
| 429 | `TOO_MANY_ATTEMPTS` | 同一帳號＋IP 連續登入失敗 5 次，鎖定 60 秒 |
| 503 | `UPSTREAM_UNAVAILABLE` / `UPSTREAM_RATE_LIMITED` / `MARKET_PRICE_UNAVAILABLE` | 外部股票 API 失敗、額度用完、暫時沒有價格 |

## 登入

| Method | Endpoint | 說明 |
|---|---|---|
| POST | `/api/auth/register` | 註冊並自動登入，body `{"username":"alice","password":"至少 8 個字元","display_name":"Alice"}`，201；第一次註冊時建立 NT$1,000,000 模擬帳戶 |
| POST | `/api/auth/login` | 登入，body `{"username":"alice","password":"…"}`；設定 HttpOnly cookie `sv_session`（SameSite=Lax，預設 7 天） |
| POST | `/api/auth/logout` | 登出：刪除 session 並清除 cookie，204 |
| GET | `/api/auth/session` | 目前登入狀態，未登入也回 200：`{"authenticated": false, "user": null}`（前端使用） |
| GET | `/api/auth/me` | 目前登入的使用者，未登入回 401 |

註冊與登入的回應：

```json
{
  "user": { "id": 1, "username": "alice", "display_name": "Alice", "created_at": "2026-10-29T14:20:11Z", "last_login_at": "2026-10-29T14:20:11Z" },
  "expires_at": "2026-11-05T14:20:11Z",
  "message": "歡迎加入，Alice！"
}
```

token 只放在 HttpOnly cookie，不會出現在回應內容；資料庫只存 token 的 SHA-256。

## 系統與市況

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/health` | 健康檢查、資料來源設定狀態、背景排程狀態 |
| GET | `/api/market/status` | 台股、美股是否在交易時段（含換算成台北時間的美股時段） |
| GET | `/api/market/overview?market=TW&period=1M&limit=12` | 大盤總覽：指數＋市值前幾大公司的報價、走勢與期間報酬（`limit` 4–30，預設 `OVERVIEW_SIZE`） |
| GET | `/api/fx/usd-twd` | USD/TWD 匯率（臺灣銀行即期中價） |

`GET /api/market/overview?market=TW` 回應（節錄，2026-10-29 收盤後實際取得的資料）：

```json
{
  "market": "TW", "period": "1M", "market_open": false,
  "indices": [
    { "rank": null, "symbol": "TAIEX", "name": "加權指數", "is_index": true,
      "quote": { "price": 46368.33, "change_pct": -1.4186, "kind": "close", "source": "TWSE MIS" },
      "points": [{ "date": "2026-09-29", "close": 47631.96 }, "…", { "date": "2026-10-29", "close": 46368.33 }],
      "period_return_pct": -2.65 }
  ],
  "stocks": [
    { "rank": 1, "symbol": "2330", "name": "台積電", "market_cap": 62885997412475.0,
      "quote": { "price": 2415.0, "change_pct": -0.4124, "kind": "close", "source": "TWSE MIS" },
      "points": [{ "date": "2026-09-29", "close": 2475.0 }, "…", { "date": "2026-10-29", "close": 2415.0 }],
      "period_return_pct": -2.42, "history_end": "2026-10-29", "history_error": null }
  ],
  "ranking": { "method": "已發行普通股數 × 收盤價", "source": "TWSE OpenAPI t187ap03_L（已發行普通股數）、STOCK_DAY_ALL（收盤價）", "as_of": "2026-10-28", "note": "…" },
  "history_source": "FinMind TaiwanStockPrice",
  "warnings": [],
  "triggered_alerts": []
}
```

- 美股（`market=US`）的指數是 `^GSPC`、`^IXIC`、`^DJI`，只有每日收盤（`kind: "close"`）
- 單一股票失敗時，該項目的 `quote` 為 null 並附 `quote_error`，或 `points` 為空並附 `history_error`；其他項目照常回傳
- 排行暫時無法取得時 `stocks` 為空、`ranking` 為 null，原因寫在 `warnings`，指數仍會回傳

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

## 自選股 🔒

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/watchlist?with_quotes=true` | 自己的自選股（附最新報價） |
| POST | `/api/watchlist` | body `{"symbol": "2330"}`，重複時回 409 |
| DELETE | `/api/watchlist/{symbol}` | 移除（204） |

## 模擬交易 🔒

每個帳號有自己的模擬帳戶，第一次使用時自動建立。

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/account` | 現金、初始資金、回合 |
| POST | `/api/account/reset` | 重置：清空持股、現金回到 NT$1,000,000、交易紀錄保留 |
| GET | `/api/portfolio` | 持股市值、未實現／已實現損益、總資產、報酬率、配置比例 |
| POST | `/api/trades/preview` | 試算（不成交），body `{"symbol":"2330","side":"BUY","shares":100}` |
| POST | `/api/trades` | 模擬成交（價格由後端取得），201 |
| GET | `/api/trades?scope=current&limit=100` | 交易紀錄；`scope=all` 包含重置前 |

## 價格提醒與通知 🔒

只能看到與修改自己的提醒與通知；別人的提醒回 404。

| Method | Endpoint | 說明 |
|---|---|---|
| GET | `/api/alerts` | 提醒清單＋背景排程狀態 |
| POST | `/api/alerts` | body `{"symbol":"2330","condition":"PRICE_LTE","target_price":900,"trigger_mode":"ONCE"}`；建立後立即檢查 |
| PATCH | `/api/alerts/{id}` | 修改條件、目標價、模式、啟用／停用（修改後重新檢查） |
| DELETE | `/api/alerts/{id}` | 刪除（觸發紀錄保留） |
| POST | `/api/alerts/check` | 立即檢查自己所有啟用中的提醒 |
| GET | `/api/alerts/events?alert_id=&limit=100` | 歷史觸發紀錄 |
| GET | `/api/alerts/monitor` | 背景排程狀態與執行條件說明 |
| GET | `/api/notifications?unread_only=false` | 站內通知與未讀數 |
| POST | `/api/notifications/{id}/read` | 標為已讀 |
| POST | `/api/notifications/read-all` | 全部標為已讀 |

行情 API（`/api/stocks/*`、`/api/market/overview`）不需要登入；登入時，回應中的 `triggered_alerts` 會帶出這次取得行情時觸發的**自己的**提醒。

`condition`：`PRICE_LTE`（價格 ≤ 目標價）、`PRICE_GTE`（價格 ≥ 目標價）、`NEW_20D_LOW`（創 20 日新低，不需目標價）。
`trigger_mode`：`ONCE`（觸發後停用）、`EVERY_CROSS`（每次由不成立變成立都通知）。

// 與 Python FastAPI 後端 Pydantic schema 對應的型別（金額以 number 傳輸，後端以 Decimal 計算）

export type Market = "TW" | "US";
export type Currency = "TWD" | "USD";
export type Period = "1M" | "3M" | "6M" | "1Y";
export type QuoteKind = "realtime" | "close";

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export interface StockInfo {
  symbol: string;
  market: Market;
  name: string;
  exchange: string;
  industry: string | null;
  currency: Currency;
}

export interface StockSearchResponse {
  query: string;
  results: StockInfo[];
  source: string;
  warnings: string[];
}

export interface Quote {
  symbol: string;
  market: Market;
  name: string;
  exchange: string;
  currency: Currency;
  price: number | null;
  change: number | null;
  change_pct: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  prev_close: number | null;
  volume: number | null;
  volume_note: string | null;
  trade_date: string | null;
  as_of: string | null;
  kind: QuoteKind;
  source: string;
  note: string | null;
  market_open: boolean;
  fetched_at: string;
}

export interface QuoteError {
  symbol: string;
  market: Market | null;
  code: string;
  message: string;
}

export interface QuotesResponse {
  quotes: Quote[];
  errors: QuoteError[];
  triggered_alerts: AlertEvent[];
}

export interface StockDetail {
  stock: StockInfo;
  quote: Quote;
  low_20d: number | null;
  is_20d_low: boolean;
  triggered_alerts: AlertEvent[];
}

export interface PriceBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  change: number | null;
  change_pct: number | null;
}

export interface HistoryStats {
  start_date: string | null;
  end_date: string | null;
  start_close: number | null;
  end_close: number | null;
  period_return_pct: number | null;
  high: number | null;
  low: number | null;
  avg_volume: number | null;
  trading_days: number;
}

export interface HistoryResponse {
  symbol: string;
  market: Market;
  name: string;
  currency: Currency;
  period: Period;
  source: string;
  data_note: string;
  fetched_at: string;
  bars: PriceBar[];
  stats: HistoryStats;
}

export interface ComparePoint {
  date: string;
  values: Record<string, number>;
  closes: Record<string, number>;
}

export interface CompareStock {
  symbol: string;
  market: Market;
  name: string;
  exchange: string;
  currency: Currency;
  latest_price: number | null;
  day_change_pct: number | null;
  volume: number | null;
  quote_kind: QuoteKind | null;
  quote_source: string | null;
  quote_as_of: string | null;
  start_close: number;
  end_close: number;
  cumulative_return_pct: number;
  max_drawdown_pct: number;
  data_points: number;
  excluded_dates: number;
}

export interface CompareResponse {
  period: Period;
  symbols: string[];
  common_start: string;
  common_end: string;
  aligned_points: number;
  method: string;
  computed_by: string;
  stocks: CompareStock[];
  series: ComparePoint[];
  errors: QuoteError[];
  triggered_alerts: AlertEvent[];
  fetched_at: string;
}

export interface MarketSession {
  market: Market;
  name: string;
  state: "open" | "pre_open" | "closed";
  label: string;
  is_open: boolean;
  local_time: string;
  timezone: string;
  session: string;
  session_taipei: string;
  note: string;
}

export interface MarketStatus {
  markets: MarketSession[];
  server_time: string;
}

export interface FxRate {
  pair: string;
  rate: number;
  spot_buy: number;
  spot_sell: number;
  rate_date: string;
  source: string;
  note: string;
  fetched_at: string;
}

export interface WatchlistItem {
  id: number;
  symbol: string;
  market: Market;
  name: string;
  exchange: string;
  currency: Currency;
  added_at: string;
  quote: Quote | null;
  quote_error: QuoteError | null;
}

export interface WatchlistResponse {
  items: WatchlistItem[];
  triggered_alerts: AlertEvent[];
}

// ---------------------------------------------------------------- 價格提醒

export type AlertCondition = "PRICE_LTE" | "PRICE_GTE" | "NEW_20D_LOW";
export type TriggerMode = "ONCE" | "EVERY_CROSS";

export interface AlertEvent {
  id: number;
  alert_id: number | null;
  symbol: string;
  market: Market;
  name: string;
  condition: AlertCondition;
  condition_label: string;
  target_price: number | null;
  triggered_price: number;
  reference_low: number | null;
  price_kind: QuoteKind;
  price_source: string;
  price_as_of: string | null;
  message: string;
  triggered_at: string;
  read_at: string | null;
}

export interface PriceAlert {
  id: number;
  symbol: string;
  market: Market;
  name: string;
  exchange: string;
  currency: Currency;
  condition: AlertCondition;
  condition_label: string;
  target_price: number | null;
  trigger_mode: TriggerMode;
  is_active: boolean;
  status: "monitoring" | "triggered" | "disabled";
  status_label: string;
  note: string | null;
  last_condition_met: boolean;
  last_checked_at: string | null;
  last_checked_price: number | null;
  last_price_kind: QuoteKind | null;
  last_triggered_at: string | null;
  trigger_count: number;
  created_at: string;
  updated_at: string;
}

export interface MonitorStatus {
  enabled: boolean;
  interval_seconds: number;
  running: boolean;
  last_run_at: string | null;
  last_result: string;
  next_run_at: string | null;
  markets_open: Market[];
  explanation: string;
}

export interface AlertList {
  alerts: PriceAlert[];
  monitor: MonitorStatus;
}

export interface AlertMutation {
  alert: PriceAlert;
  triggered: AlertEvent[];
}

export interface AlertCheck {
  checked_alerts: number;
  checked_symbols: number;
  triggered: AlertEvent[];
  errors: string[];
  checked_at: string;
}

export interface AlertInput {
  symbol: string;
  condition: AlertCondition;
  target_price: number | null;
  trigger_mode: TriggerMode;
  note: string | null;
}

export interface Notifications {
  items: AlertEvent[];
  unread_count: number;
}

// ---------------------------------------------------------------- 模擬交易

export type TradeSide = "BUY" | "SELL";

export interface Account {
  id: number;
  base_currency: string;
  initial_cash: number;
  cash: number;
  cycle: number;
  created_at: string;
  reset_at: string | null;
}

export interface Trade {
  id: number;
  cycle: number;
  symbol: string;
  market: Market;
  name: string;
  side: TradeSide;
  shares: number;
  price: number;
  currency: Currency;
  fx_rate: number;
  fx_date: string | null;
  gross_amount: number;
  amount_twd: number;
  fee_twd: number;
  tax_twd: number;
  realized_pnl_twd: number | null;
  cash_after_twd: number;
  price_kind: QuoteKind;
  price_source: string;
  price_as_of: string | null;
  created_at: string;
}

export interface TradeRequest {
  symbol: string;
  side: TradeSide;
  shares: number;
}

export interface TradePreview {
  symbol: string;
  market: Market;
  name: string;
  side: TradeSide;
  shares: number;
  price: number;
  currency: Currency;
  price_kind: QuoteKind;
  price_source: string;
  price_as_of: string | null;
  fx_rate: number;
  fx_date: string | null;
  gross_amount: number;
  amount_twd: number;
  fee_twd: number;
  tax_twd: number;
  cash_before: number;
  cash_after: number | null;
  shares_held: number;
  shares_after: number | null;
  estimated_realized_pnl_twd: number | null;
  can_execute: boolean;
  reason: string | null;
  reason_code: string | null;
  disclaimer: string;
}

export interface TradeResult {
  message: string;
  trade: Trade;
  account: Account;
  disclaimer: string;
}

export interface TradeList {
  scope: "current" | "all";
  current_cycle: number;
  trades: Trade[];
}

export interface Position {
  symbol: string;
  market: Market;
  name: string;
  exchange: string;
  currency: Currency;
  shares: number;
  avg_cost: number;
  cost_basis_twd: number;
  current_price: number | null;
  day_change_pct: number | null;
  price_kind: QuoteKind | null;
  price_source: string | null;
  price_as_of: string | null;
  fx_rate: number | null;
  market_value: number | null;
  market_value_twd: number | null;
  unrealized_pnl_twd: number | null;
  unrealized_pnl_pct: number | null;
  realized_pnl_twd: number;
  weight_pct: number | null;
  quote_error: string | null;
}

export interface Portfolio {
  account: Account;
  positions: Position[];
  cash_twd: number;
  market_value_twd: number;
  cost_basis_twd: number;
  unrealized_pnl_twd: number;
  realized_pnl_twd: number;
  total_assets_twd: number;
  total_pnl_twd: number;
  roi_pct: number | null;
  fx: FxRate | null;
  incomplete: boolean;
  warnings: string[];
  as_of: string;
  disclaimer: string;
}

export interface ResetResult {
  message: string;
  account: Account;
}

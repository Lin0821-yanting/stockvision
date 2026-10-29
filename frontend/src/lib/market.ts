import type { Market } from "@/types/api";

/** 與後端相同的判斷：數字開頭是台股，其餘是美股 */
export function marketOf(symbol: string): Market {
  return /^\d/.test(symbol.trim()) ? "TW" : "US";
}

export const MARKET_LABEL: Record<Market, string> = { TW: "台股", US: "美股" };
export const MARKET_TIMEZONE: Record<Market, string> = { TW: "Asia/Taipei", US: "America/New_York" };
export const MARKET_TZ_LABEL: Record<Market, string> = { TW: "台北時間", US: "紐約時間" };

export function exchangeLabel(exchange: string): string {
  if (exchange === "TWSE") return "上市";
  if (exchange === "TPEx") return "上櫃";
  return "美股";
}

/** 交易時段報價每 10 秒更新；非交易時段改成每 5 分鐘確認一次 */
export const LIVE_REFRESH_MS = 10_000;
export const IDLE_REFRESH_MS = 5 * 60_000;
/** 大盤總覽一次載入 15 檔的報價與走勢，盤中改成每 30 秒更新 */
export const OVERVIEW_LIVE_REFRESH_MS = 30_000;

export const POPULAR_SYMBOLS: { symbol: string; name: string }[] = [
  { symbol: "2330", name: "台積電" },
  { symbol: "2317", name: "鴻海" },
  { symbol: "2454", name: "聯發科" },
  { symbol: "0050", name: "元大台灣50" },
  { symbol: "AAPL", name: "Apple" },
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "TSLA", name: "Tesla" },
  { symbol: "MSFT", name: "Microsoft" },
];

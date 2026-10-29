import type {
  CompareResponse,
  FxRate,
  HistoryResponse,
  Market,
  MarketStatus,
  Period,
  QuotesResponse,
  StockDetail,
  StockSearchResponse,
} from "@/types/api";

import { apiRequest } from "./api-client";

export const stocksApi = {
  search: (q: string, market?: Market, limit = 8) =>
    apiRequest<StockSearchResponse>("/api/stocks/search", { query: { q, market, limit } }),
  detail: (symbol: string) => apiRequest<StockDetail>(`/api/stocks/${encodeURIComponent(symbol)}`),
  history: (symbol: string, period: Period) =>
    apiRequest<HistoryResponse>(`/api/stocks/${encodeURIComponent(symbol)}/history`, { query: { period } }),
  quotes: (symbols: string[]) => apiRequest<QuotesResponse>("/api/stocks/quotes", { query: { symbols: symbols.join(",") } }),
  compare: (symbols: string[], period: Period) =>
    apiRequest<CompareResponse>("/api/stocks/compare", { query: { symbols: symbols.join(","), period } }),
};

export const marketApi = {
  status: () => apiRequest<MarketStatus>("/api/market/status"),
  usdTwd: () => apiRequest<FxRate>("/api/fx/usd-twd"),
};

import type { Account, Portfolio, ResetResult, TradeList, TradePreview, TradeRequest, TradeResult } from "@/types/api";

import { apiRequest } from "./api-client";

export const tradingApi = {
  account: () => apiRequest<Account>("/api/account"),
  portfolio: () => apiRequest<Portfolio>("/api/portfolio"),
  preview: (request: TradeRequest) => apiRequest<TradePreview>("/api/trades/preview", { method: "POST", json: request }),
  execute: (request: TradeRequest) => apiRequest<TradeResult>("/api/trades", { method: "POST", json: request }),
  trades: (scope: "current" | "all" = "current", limit = 100) =>
    apiRequest<TradeList>("/api/trades", { query: { scope, limit } }),
  reset: () => apiRequest<ResetResult>("/api/account/reset", { method: "POST" }),
};

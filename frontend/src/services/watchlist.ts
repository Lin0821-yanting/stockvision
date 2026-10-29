import type { WatchlistItem, WatchlistResponse } from "@/types/api";

import { apiRequest } from "./api-client";

export const watchlistApi = {
  list: () => apiRequest<WatchlistResponse>("/api/watchlist"),
  add: (symbol: string) => apiRequest<WatchlistItem>("/api/watchlist", { method: "POST", json: { symbol } }),
  remove: (symbol: string) => apiRequest<void>(`/api/watchlist/${encodeURIComponent(symbol)}`, { method: "DELETE" }),
};

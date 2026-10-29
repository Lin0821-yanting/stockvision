"use client";

import { useCallback } from "react";
import useSWR, { useSWRConfig } from "swr";

import { IDLE_REFRESH_MS, LIVE_REFRESH_MS } from "@/lib/market";
import { tradingApi } from "@/services/trading";

import { useMarketStatus } from "./use-market";

export const PORTFOLIO_KEY = "portfolio";

export function usePortfolio() {
  const { data: status } = useMarketStatus();
  const openMarkets = new Set(status?.markets.filter((session) => session.is_open).map((session) => session.market));
  return useSWR(PORTFOLIO_KEY, () => tradingApi.portfolio(), {
    keepPreviousData: true,
    // 持有的股票所在市場開盤時每 10 秒重新估值，否則 5 分鐘
    refreshInterval: (latest) =>
      latest?.positions.some((position) => openMarkets.has(position.market)) ? LIVE_REFRESH_MS : IDLE_REFRESH_MS,
  });
}

export function useTrades(scope: "current" | "all" = "current", limit = 100) {
  return useSWR(["trades", scope, limit], () => tradingApi.trades(scope, limit), { keepPreviousData: true });
}

/** 交易或重置後，更新所有和帳戶有關的畫面 */
export function useRefreshAccountData() {
  const { mutate } = useSWRConfig();
  // 只傳 filter（不傳資料）時 SWR 只會重新驗證，畫面保留舊資料不閃爍
  return useCallback(
    () =>
      mutate(
        (key) => key === PORTFOLIO_KEY || (Array.isArray(key) && (key[0] === "trades" || key[0] === "trade-preview")),
      ),
    [mutate],
  );
}

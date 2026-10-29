"use client";

import { useCallback } from "react";
import useSWR from "swr";
import { toast } from "sonner";

import { IDLE_REFRESH_MS, LIVE_REFRESH_MS } from "@/lib/market";
import { errorMessage } from "@/services/api-client";
import { watchlistApi } from "@/services/watchlist";

import { useAlertTriggerHandler } from "./use-alerts";
import { useMarketStatus } from "./use-market";

export const WATCHLIST_KEY = "watchlist";

export function useWatchlist() {
  const { data: status } = useMarketStatus();
  const openMarkets = new Set(status?.markets.filter((session) => session.is_open).map((session) => session.market));
  const onSuccess = useAlertTriggerHandler();

  const swr = useSWR(WATCHLIST_KEY, () => watchlistApi.list(), {
    keepPreviousData: true,
    onSuccess,
    // 自選股中有任一市場在交易時段就每 10 秒更新報價
    refreshInterval: (latest) =>
      latest?.items.some((item) => openMarkets.has(item.market)) ? LIVE_REFRESH_MS : IDLE_REFRESH_MS,
  });
  const { data, mutate } = swr;

  const add = useCallback(
    async (symbol: string) => {
      try {
        const item = await watchlistApi.add(symbol);
        toast.success(`已將 ${item.symbol} ${item.name} 加入自選股`);
        await mutate();
        return true;
      } catch (error) {
        toast.error(errorMessage(error));
        return false;
      }
    },
    [mutate],
  );

  const remove = useCallback(
    async (symbol: string) => {
      try {
        await watchlistApi.remove(symbol);
        toast.success(`已將 ${symbol} 從自選股移除`);
        await mutate();
        return true;
      } catch (error) {
        toast.error(errorMessage(error));
        return false;
      }
    },
    [mutate],
  );

  const has = useCallback(
    (symbol: string) => data?.items.some((item) => item.symbol === symbol.toUpperCase()) ?? false,
    [data],
  );

  return { ...swr, add, remove, has };
}

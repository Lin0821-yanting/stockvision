"use client";

import useSWR from "swr";

import { IDLE_REFRESH_MS, LIVE_REFRESH_MS, marketOf } from "@/lib/market";
import { marketApi, stocksApi } from "@/services/stocks";
import type { Market, Period } from "@/types/api";

import { useAlertTriggerHandler } from "./use-alerts";

export function useMarketStatus() {
  return useSWR("market-status", () => marketApi.status(), { refreshInterval: 60_000 });
}

/** 指定市場有任何一個在交易時段，就用 10 秒輪詢；否則 5 分鐘 */
export function useRefreshInterval(markets: Market[]): number {
  const { data } = useMarketStatus();
  const open = data?.markets.some((session) => markets.includes(session.market) && session.is_open) ?? false;
  return open ? LIVE_REFRESH_MS : IDLE_REFRESH_MS;
}

export function useStockDetail(symbol: string | null) {
  const refreshInterval = useRefreshInterval(symbol ? [marketOf(symbol)] : []);
  const onSuccess = useAlertTriggerHandler();
  return useSWR(symbol ? ["stock", symbol] : null, () => stocksApi.detail(symbol!), {
    refreshInterval,
    keepPreviousData: true,
    onSuccess,
  });
}

export function useHistory(symbol: string | null, period: Period) {
  return useSWR(symbol ? ["history", symbol, period] : null, () => stocksApi.history(symbol!, period), {
    keepPreviousData: true,
    revalidateOnFocus: false,
  });
}

export function useQuotes(symbols: string[]) {
  const key = symbols.length ? ["quotes", ...symbols] : null;
  const refreshInterval = useRefreshInterval(symbols.map(marketOf));
  const onSuccess = useAlertTriggerHandler();
  return useSWR(key, () => stocksApi.quotes(symbols), { refreshInterval, keepPreviousData: true, onSuccess });
}

export function useCompare(symbols: string[], period: Period) {
  const onSuccess = useAlertTriggerHandler();
  const key = symbols.length >= 2 ? ["compare", period, ...symbols] : null;
  return useSWR(key, () => stocksApi.compare(symbols, period), {
    keepPreviousData: true,
    revalidateOnFocus: false,
    onSuccess,
  });
}

export function useUsdTwd() {
  return useSWR("fx-usd-twd", () => marketApi.usdTwd(), { refreshInterval: 30 * 60_000 });
}

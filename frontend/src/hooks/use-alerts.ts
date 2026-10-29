"use client";

import { useCallback } from "react";
import useSWR, { useSWRConfig } from "swr";

import { alertsApi, notificationsApi } from "@/services/alerts";
import type { AlertEvent } from "@/types/api";

export const ALERTS_KEY = "alerts";
export const ALERT_EVENTS_KEY = "alert-events";
export const NOTIFICATIONS_KEY = "notifications";

export function useAlerts() {
  return useSWR(ALERTS_KEY, () => alertsApi.list(), { refreshInterval: 30_000, keepPreviousData: true });
}

export function useAlertEvents() {
  return useSWR(ALERT_EVENTS_KEY, () => alertsApi.events(100), { refreshInterval: 30_000, keepPreviousData: true });
}

export function useNotifications() {
  return useSWR(NOTIFICATIONS_KEY, () => notificationsApi.list(20), { refreshInterval: 20_000, keepPreviousData: true });
}

/** 提醒有變化（建立、觸發、已讀）時，更新提醒清單、觸發紀錄與通知鈴鐺 */
export function useRefreshAlerts() {
  const { mutate } = useSWRConfig();
  return useCallback(
    () => mutate((key) => key === ALERTS_KEY || key === ALERT_EVENTS_KEY || key === NOTIFICATIONS_KEY),
    [mutate],
  );
}

/** 給行情相關的 SWR onSuccess 使用：回應中有新觸發的提醒就立刻更新通知 */
export function useAlertTriggerHandler() {
  const refresh = useRefreshAlerts();
  return useCallback(
    (data: { triggered_alerts?: AlertEvent[] } | undefined) => {
      if (data?.triggered_alerts?.length) void refresh();
    },
    [refresh],
  );
}

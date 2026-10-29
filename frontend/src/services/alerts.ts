import type { AlertCheck, AlertEvent, AlertInput, AlertList, AlertMutation, Notifications } from "@/types/api";

import { apiRequest } from "./api-client";

export const alertsApi = {
  list: () => apiRequest<AlertList>("/api/alerts"),
  create: (input: AlertInput) => apiRequest<AlertMutation>("/api/alerts", { method: "POST", json: input }),
  update: (id: number, changes: Partial<Omit<AlertInput, "symbol">> & { is_active?: boolean }) =>
    apiRequest<AlertMutation>(`/api/alerts/${id}`, { method: "PATCH", json: changes }),
  remove: (id: number) => apiRequest<void>(`/api/alerts/${id}`, { method: "DELETE" }),
  check: () => apiRequest<AlertCheck>("/api/alerts/check", { method: "POST" }),
  events: (limit = 100) => apiRequest<AlertEvent[]>("/api/alerts/events", { query: { limit } }),
};

export const notificationsApi = {
  list: (limit = 20) => apiRequest<Notifications>("/api/notifications", { query: { limit } }),
  read: (id: number) => apiRequest<AlertEvent>(`/api/notifications/${id}/read`, { method: "POST" }),
  readAll: () => apiRequest<{ updated: number }>("/api/notifications/read-all", { method: "POST" }),
};

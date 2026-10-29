import type { AuthResponse, SessionInfo } from "@/types/api";

import { apiRequest } from "./api-client";

export const authApi = {
  // 未登入也回 200，瀏覽器主控台不會每頁都出現 401
  session: () => apiRequest<SessionInfo>("/api/auth/session"),
  login: (username: string, password: string) =>
    apiRequest<AuthResponse>("/api/auth/login", { method: "POST", json: { username, password } }),
  register: (username: string, password: string, displayName?: string) =>
    apiRequest<AuthResponse>("/api/auth/register", {
      method: "POST",
      json: { username, password, display_name: displayName?.trim() || null },
    }),
  logout: () => apiRequest<void>("/api/auth/logout", { method: "POST" }),
};

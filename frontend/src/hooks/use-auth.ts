"use client";

import { useCallback } from "react";
import useSWR, { mutate as mutateCache } from "swr";

import { authApi } from "@/services/auth";
import type { User } from "@/types/api";

export const AUTH_KEY = "auth-session";

/** 個人資料的 SWR key：切換帳號時要清空，避免短暫顯示上一位使用者的資料 */
const PERSONAL_KEYS = new Set(["watchlist", "portfolio", "alerts", "alert-events", "notifications"]);
const PERSONAL_PREFIXES = new Set(["trades", "trade-preview"]);

export function isPersonalKey(key: unknown): boolean {
  if (typeof key === "string") return PERSONAL_KEYS.has(key);
  return Array.isArray(key) && PERSONAL_PREFIXES.has(key[0]);
}

// 目前畫面對應的使用者；undefined 代表還沒確認過登入狀態
let knownUserId: number | null | undefined;

/** 使用者變了（登入、登出，或在其他分頁換了帳號）就先清掉個人資料快取，再更新登入狀態 */
async function syncIdentity(user: User | null) {
  const id = user?.id ?? null;
  if (knownUserId !== undefined && knownUserId !== id) {
    await mutateCache(isPersonalKey, undefined, { revalidate: false });
  }
  knownUserId = id;
}

async function fetchCurrentUser(): Promise<User | null> {
  const { user } = await authApi.session();
  await syncIdentity(user);
  return user;
}

export function useAuth() {
  const { data, error, mutate } = useSWR(AUTH_KEY, fetchCurrentUser);

  const signIn = useCallback(
    async (user: User) => {
      await syncIdentity(user);
      await mutate(user, { revalidate: false });
    },
    [mutate],
  );

  const login = useCallback(
    async (username: string, password: string) => {
      const result = await authApi.login(username, password);
      await signIn(result.user);
      return result;
    },
    [signIn],
  );

  const register = useCallback(
    async (username: string, password: string, displayName?: string) => {
      const result = await authApi.register(username, password, displayName);
      await signIn(result.user);
      return result;
    },
    [signIn],
  );

  const logout = useCallback(async () => {
    await authApi.logout();
    await syncIdentity(null);
    await mutate(null, { revalidate: false });
  }, [mutate]);

  const retry = useCallback(() => void mutate(), [mutate]);

  return {
    user: data ?? null,
    isLoading: data === undefined && !error,
    error,
    retry,
    login,
    register,
    logout,
  };
}

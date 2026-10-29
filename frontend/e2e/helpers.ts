import type { APIRequestContext, Page } from "@playwright/test";

export const API = "http://localhost:8001";
export const PASSWORD = "e2e-password-42";

let sequence = 0;

/** 每次執行都不重複的帳號（E2E 資料庫會保留上一次執行的使用者） */
export function uniqueUsername(prefix = "e2e"): string {
  sequence += 1;
  return `${prefix}_${Date.now().toString(36)}${sequence}${Math.random().toString(36).slice(2, 5)}`;
}

/**
 * 透過 Python API 註冊新帳號。傳入 page.request 時 cookie 和瀏覽器共用，之後開的頁面就是已登入狀態；
 * 每個測試都用自己的新帳號，資料天生互相隔離，不需要再清空資料庫。
 */
export async function registerUser(request: APIRequestContext, username = uniqueUsername(), displayName = username) {
  const response = await request.post(`${API}/api/auth/register`, {
    data: { username, password: PASSWORD, display_name: displayName },
  });
  if (!response.ok()) throw new Error(`註冊測試帳號失敗：HTTP ${response.status()} ${await response.text()}`);
  return { username, password: PASSWORD, displayName };
}

export async function noHorizontalOverflow(page: Page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
}

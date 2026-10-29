import type { APIRequestContext, Page } from "@playwright/test";

export const API = "http://localhost:8001";

/** 每個測試開始前把 E2E 資料庫整理成乾淨狀態（透過 Python API，不直接刪檔案） */
export async function resetState(request: APIRequestContext) {
  await request.post(`${API}/api/account/reset`);
  const watchlist = await (await request.get(`${API}/api/watchlist?with_quotes=false`)).json();
  for (const item of watchlist.items) await request.delete(`${API}/api/watchlist/${item.symbol}`);
  const alerts = await (await request.get(`${API}/api/alerts`)).json();
  for (const alert of alerts.alerts) await request.delete(`${API}/api/alerts/${alert.id}`);
  await request.post(`${API}/api/notifications/read-all`);
}

export async function noHorizontalOverflow(page: Page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
}

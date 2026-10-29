import { request } from "@playwright/test";

import { API, registerUser, uniqueUsername } from "./helpers";

/**
 * 舊版單人模式留下的資料會交給「第一位註冊者」。
 * 測試開始前先註冊一個帳號接收這些資料，之後每個測試的新帳號都是乾淨的 NT$1,000,000 帳戶。
 * （Playwright 會先啟動 webServer 再執行 globalSetup。）
 */
export default async function globalSetup() {
  const context = await request.newContext({ baseURL: API });
  try {
    await registerUser(context, uniqueUsername("legacy"));
  } finally {
    await context.dispose();
  }
}

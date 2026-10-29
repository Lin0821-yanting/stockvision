import path from "node:path";

import { defineConfig, devices } from "@playwright/test";

/**
 * 端對端測試：使用電腦已安裝的 Microsoft Edge（不另外下載瀏覽器）。
 * 測試時另外啟動一組伺服器，不會動到開發用的資料：
 *   後端 http://localhost:8001（backend/data/e2e.db、關閉背景排程）
 *   前端 http://localhost:3001（建置到 .next-e2e）
 * 後端需要真實網路取得股票資料；Python 路徑可用 STOCKVISION_PYTHON 指定，
 * 預設使用目前環境的 python（請先 conda activate stockvision）。
 */
const BACKEND_PORT = 8001;
const FRONTEND_PORT = 3001;
const E2E_API_URL = `http://localhost:${BACKEND_PORT}`;
const python = process.env.STOCKVISION_PYTHON ?? "python";

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    locale: "zh-TW",
    timezoneId: "Asia/Taipei",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "edge", use: { ...devices["Desktop Edge"], channel: "msedge" } }],
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: path.resolve(__dirname, "../backend"),
      url: `${E2E_API_URL}/api/health`,
      env: {
        ...(process.env as Record<string, string>),
        DATABASE_URL: "sqlite:///./data/e2e.db",
        CORS_ORIGINS: `http://localhost:${FRONTEND_PORT}`,
        ALERT_SCHEDULER_ENABLED: "false",
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npm run build && npm run start -- --port ${FRONTEND_PORT}`,
      url: `http://localhost:${FRONTEND_PORT}`,
      env: {
        ...(process.env as Record<string, string>),
        NEXT_PUBLIC_API_BASE_URL: E2E_API_URL,
        NEXT_DIST_DIR: ".next-e2e",
      },
      reuseExistingServer: false,
      timeout: 300_000,
    },
  ],
});

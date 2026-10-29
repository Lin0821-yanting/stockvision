import { expect, test } from "@playwright/test";

import { noHorizontalOverflow, registerUser } from "./helpers";

test.describe("API 失敗時的提示", () => {
  test("外部股票 API 失敗時顯示後端回報的錯誤，而不是假資料", async ({ page }) => {
    await page.route("**/api/stocks/2330**", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ error: { code: "UPSTREAM_UNAVAILABLE", message: "無法從 FinMind 取得資料：連線逾時", details: {} } }),
      }),
    );
    await page.goto("/market?symbol=2330");

    const alert = page.getByRole("alert").filter({ hasText: "無法從 FinMind 取得資料：連線逾時" }).first();
    await expect(alert).toBeVisible();
    await expect(alert).toContainText("UPSTREAM_UNAVAILABLE");
    await expect(page.getByTestId("quote-price")).toHaveCount(0);
  });

  test("後端無法連線時提示啟動 Python 服務", async ({ page }) => {
    await registerUser(page.request);
    await page.route("**/api/portfolio", (route) => route.abort("connectionrefused"));
    await page.goto("/portfolio");

    await expect(page.getByRole("alert").first()).toContainText("無法連線到 StockVision 後端");
    await expect(page.getByRole("button", { name: "重新載入" }).first()).toBeVisible();
  });

  test("確認登入狀態失敗時顯示錯誤，而不是要求登入", async ({ page }) => {
    await page.route("**/api/auth/session", (route) => route.abort("connectionrefused"));
    await page.goto("/trading");

    await expect(page.getByRole("alert").filter({ hasText: "無法確認登入狀態" })).toBeVisible();
    await expect(page.getByText("請先登入")).toHaveCount(0);
  });
});

test.describe("手機版排版", () => {
  test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });

  test.beforeEach(async ({ page }) => {
    await registerUser(page.request);
  });

  test("漢堡選單可以開啟導覽", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "開啟選單" }).click();

    const dialog = page.getByRole("dialog");
    await dialog.getByRole("link", { name: /模擬下單/ }).click();
    await expect(page).toHaveURL(/\/trading/);
  });

  for (const path of ["/", "/overview", "/market?symbol=2330", "/compare?symbols=2330,2317", "/trading", "/portfolio", "/alerts"]) {
    test(`${path} 沒有水平捲動`, async ({ page }) => {
      await page.goto(path);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await page.waitForLoadState("networkidle");

      expect(await noHorizontalOverflow(page)).toBe(true);
    });
  }
});

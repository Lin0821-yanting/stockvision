import { expect, test } from "@playwright/test";

const PAGES = [
  { path: "/", heading: "投資總覽" },
  { path: "/market", heading: "股票看盤" },
  { path: "/compare", heading: "股票比較" },
  { path: "/trading", heading: "模擬下單" },
  { path: "/portfolio", heading: "投資組合" },
  { path: "/alerts", heading: "價格提醒" },
];

test.describe("主要頁面", () => {
  for (const { path, heading } of PAGES) {
    test(`${heading}（${path}）正常載入`, async ({ page }) => {
      const errors: string[] = [];
      page.on("pageerror", (error) => errors.push(String(error)));

      await page.goto(path);

      await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
      await expect(page.getByRole("alert").filter({ hasText: "資料載入失敗" })).toHaveCount(0);
      expect(errors).toEqual([]);
    });
  }

  test("側邊欄可以切換頁面", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("navigation", { name: "主要導覽" }).getByRole("link", { name: /股票比較/ }).click();

    await expect(page).toHaveURL(/\/compare/);
    await expect(page.getByRole("heading", { level: 1, name: "股票比較" })).toBeVisible();
  });

  test("前端成功呼叫 Python 後端", async ({ page }) => {
    const response = page.waitForResponse((res) => res.url().includes("/api/market/status") && res.ok());
    await page.goto("/");

    expect((await response).status()).toBe(200);
    await expect(page.getByTestId("market-status").first()).toContainText("台股");
  });
});

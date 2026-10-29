import { expect, test } from "@playwright/test";

import { resetState } from "./helpers";

test.beforeEach(async ({ request }) => {
  await resetState(request);
});

test("搜尋 2330 顯示台積電的真實報價與資料來源", async ({ page }) => {
  await page.goto("/market");
  await page.getByRole("main").getByRole("combobox", { name: "搜尋股票" }).fill("台積電");
  await page.getByRole("option", { name: /2330/ }).click();

  await expect(page).toHaveURL(/symbol=2330/);
  const card = page.getByTestId("quote-card");
  await expect(card.getByRole("heading", { name: "台積電" })).toBeVisible();
  await expect(page.getByTestId("quote-price")).toHaveText(/\d{1,3}(,\d{3})*\.\d{2}/);
  await expect(page.getByTestId("data-source")).toContainText(/來源：(TWSE MIS|FinMind TaiwanStockPrice|TWSE OpenAPI)/);
  await expect(page.getByTestId("data-source")).toContainText("資料日期");
});

test("切換 1 個月與 1 年時圖表跟著資料更新", async ({ page }) => {
  await page.goto("/market?symbol=2330");
  const chart = page.getByTestId("price-chart");
  await expect(chart).toBeVisible();

  await page.getByRole("tab", { name: "1 個月" }).click();
  await expect.poll(async () => Number(await chart.getAttribute("data-points"))).toBeLessThan(30);
  const monthPoints = Number(await chart.getAttribute("data-points"));

  await page.getByRole("tab", { name: "1 年" }).click();
  await expect.poll(async () => Number(await chart.getAttribute("data-points"))).toBeGreaterThan(200);
  expect(monthPoints).toBeGreaterThan(10);

  await page.getByRole("tab", { name: "資料表" }).click();
  await expect(page.getByRole("main").locator("table tbody tr").first()).toBeVisible();
});

test("加入自選股後重新整理仍然存在", async ({ page }) => {
  await page.goto("/market?symbol=2317");
  const toggle = page.getByTestId("watchlist-toggle");
  await expect(toggle).toHaveText(/加入自選/);

  await toggle.click();
  await expect(toggle).toHaveText(/移除自選/);
  await page.reload();

  await expect(page.getByTestId("watchlist-toggle")).toHaveText(/移除自選/);
  await expect(page.getByTestId("watchlist-panel")).toContainText("鴻海");
});

test("找不到的代號顯示明確的錯誤，且只顯示一次", async ({ page }) => {
  await page.goto("/market?symbol=9999");

  const errors = page.getByRole("alert").filter({ hasText: "找不到股票代號 9999" });
  await expect(errors).toHaveCount(1);
  await expect(errors).toContainText("SYMBOL_NOT_FOUND");
  await expect(page.getByTestId("price-chart")).toHaveCount(0);
});

import { expect, test } from "@playwright/test";

import { API, registerUser } from "./helpers";

test("建立已成立的提醒會立即觸發並出現站內通知", async ({ page }) => {
  await registerUser(page.request);
  await page.goto("/alerts?symbol=2330");
  const form = page.getByTestId("alert-form");
  await expect(form.getByText("目前價格")).toBeVisible();
  await page.getByLabel("目標價格").fill("1000000");
  await page.getByTestId("save-alert").click();

  await expect(page.getByText(/已建立提醒：台積電 價格 ≤ 1,000,000.00 TWD（條件已成立/).first()).toBeVisible();
  await expect(page.getByTestId("notification-bell")).toHaveAttribute("aria-label", /1 則未讀/);
  await expect(page.getByTestId("alerts-table")).toContainText("已觸發（已停用）");
  await expect(page.getByTestId("alert-events")).toContainText("台積電");
});

test("提醒可以停用與刪除", async ({ page }) => {
  await registerUser(page.request);
  await page.request.post(`${API}/api/alerts`, { data: { symbol: "2330", condition: "PRICE_LTE", target_price: 1 } });
  await page.goto("/alerts");
  const row = page.getByTestId("alerts-table").locator("tbody tr").first();
  await expect(row).toContainText("監控中");

  await row.getByRole("switch").click();
  await expect(row).toContainText("已停用");

  await row.getByRole("button", { name: /刪除/ }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "刪除" }).click();
  await expect(page.getByText("還沒有價格提醒")).toBeVisible();
});

test("比較台積電與鴻海：Pandas 標準化走勢與比較表", async ({ page }) => {
  await page.goto("/compare?symbols=2330,2317&period=3M");
  const chart = page.getByTestId("compare-chart");

  await expect(chart).toHaveAttribute("data-series", "2");
  await expect(page.getByTestId("compare-method")).toContainText("Python Pandas");
  await expect(page.getByTestId("compare-table")).toContainText("台積電");
  await expect(page.getByTestId("compare-table")).toContainText("鴻海");
  const threeMonths = Number(await chart.getAttribute("data-points"));

  await page.getByRole("tab", { name: "1 年" }).click();
  await expect.poll(async () => Number(await chart.getAttribute("data-points"))).toBeGreaterThan(threeMonths);
});

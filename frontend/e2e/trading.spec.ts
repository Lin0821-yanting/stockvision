import { expect, test } from "@playwright/test";

import { resetState } from "./helpers";

test.beforeEach(async ({ request }) => {
  await resetState(request);
});

test("資金不足時無法下單並顯示原因", async ({ page }) => {
  await page.goto("/trading?symbol=2330");
  await page.getByLabel("股數").fill("1000");

  await expect(page.getByTestId("preview-reason")).toContainText("可用資金不足");
  await expect(page.getByTestId("submit-trade")).toBeDisabled();
});

test("模擬買進後帳戶與持股更新，重新整理後仍存在", async ({ page }) => {
  await page.goto("/trading?symbol=2330");
  await expect(page.getByTestId("account-cash")).toHaveText("NT$ 1,000,000");
  await page.getByLabel("股數").fill("100");
  await expect(page.getByTestId("trade-preview")).toContainText("→ 100 股");

  await page.getByTestId("submit-trade").click();
  await expect(page.getByRole("alertdialog")).toContainText("模擬成交，不代表真實市場價格或成交");
  await page.getByTestId("confirm-trade").click();

  await expect(page.getByText(/模擬買進 2330 台積電 100 股/).first()).toBeVisible();
  await expect(page.getByTestId("account-cash")).not.toHaveText("NT$ 1,000,000");
  await expect(page.getByTestId("holding-card")).toContainText("100 股");
  const cashAfter = await page.getByTestId("account-cash").textContent();

  await page.reload();
  await expect(page.getByTestId("account-cash")).toHaveText(cashAfter!);

  await page.goto("/portfolio");
  await expect(page.getByTestId("positions-table")).toContainText("台積電");
  await expect(page.getByTestId("trade-history")).toContainText("買進");
});

test("賣出超過持股會被拒絕，全部賣出後持股清空", async ({ page, request }) => {
  await request.post("http://localhost:8001/api/trades", { data: { symbol: "2317", side: "BUY", shares: 10 } });
  await page.goto("/trading?symbol=2317");
  await page.getByRole("radio", { name: "賣出" }).click();
  await page.getByLabel("股數").fill("11");
  await expect(page.getByTestId("preview-reason")).toContainText("持股不足");

  await page.getByRole("button", { name: /全部 10 股/ }).click();
  await expect(page.getByTestId("trade-preview")).toContainText("→ 0 股");
  await page.getByTestId("submit-trade").click();
  await page.getByTestId("confirm-trade").click();

  await expect(page.getByText(/模擬賣出 2317 鴻海 10 股/).first()).toBeVisible();
  await expect(page.getByRole("main")).toContainText("尚未持有這檔股票");
});

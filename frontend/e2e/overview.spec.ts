import { expect, test, type Page } from "@playwright/test";

// 第一次載入要向 FinMind 取 13～15 檔的日資料，給比較長的等待時間
const FIRST_LOAD = { timeout: 75_000 };

function panel(page: Page, market: "TW" | "US") {
  return page.getByTestId(`overview-${market}`);
}

test("台股頁有加權指數與市值前 12 大公司的走勢", async ({ page }) => {
  await page.goto("/overview");
  const tw = panel(page, "TW");
  await expect(tw.getByTestId("overview-stock")).toHaveCount(12, FIRST_LOAD);

  await expect(tw.getByTestId("overview-index")).toContainText("加權指數");
  await expect(tw.getByTestId("overview-stock").first()).toContainText("#1");
  await expect(tw.getByTestId("overview-stock").first()).toContainText("市值 NT$");
  const points = Number(await tw.getByTestId("sparkline").nth(1).getAttribute("data-points"));
  expect(points).toBeGreaterThan(10);
  await expect(tw).toContainText("已發行普通股數 × 收盤價");
  // 還沒切到美股時不會載入美股資料
  await expect(panel(page, "US").getByTestId("overview-stock")).toHaveCount(0);
});

test("點切換鈕、滑鼠拖曳與方向鍵都能切換市場", async ({ page }) => {
  await page.goto("/overview");
  const slider = page.getByTestId("market-slider");
  await expect(panel(page, "TW").getByTestId("overview-stock")).toHaveCount(12, FIRST_LOAD);

  await page.getByRole("tab", { name: "美股" }).click();
  await expect(slider).toHaveAttribute("data-page", "US");
  await expect(page).toHaveURL(/market=US/);
  const us = panel(page, "US");
  await expect(us.getByTestId("overview-stock")).toHaveCount(12, FIRST_LOAD);
  await expect(us.getByTestId("overview-index")).toHaveCount(3);
  await expect(us.getByTestId("overview-index").first()).toContainText("收盤");

  // 從卡片上往右拖回台股，放開後不會誤點進看盤頁
  const box = (await slider.boundingBox())!;
  const y = box.y + 360;
  await page.mouse.move(box.x + box.width * 0.3, y);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.3 + 240, y + 6, { steps: 12 });
  await page.mouse.up();
  await expect(slider).toHaveAttribute("data-page", "TW");
  await expect(page).toHaveURL(/\/overview$/);

  await page.getByRole("tab", { name: "台股" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(slider).toHaveAttribute("data-page", "US");
  await expect(page.locator("#overview-panel-TW")).toHaveJSProperty("inert", true);
});

test("切換期間時走勢資料點跟著改變，也可以改用表格檢視", async ({ page }) => {
  await page.goto("/overview");
  const tw = panel(page, "TW");
  await expect(tw.getByTestId("overview-stock")).toHaveCount(12, FIRST_LOAD);
  const sparkline = tw.getByTestId("sparkline").nth(1);
  const monthPoints = Number(await sparkline.getAttribute("data-points"));

  await page.getByRole("tab", { name: "1 年" }).click();
  await expect(tw).toHaveAttribute("data-period", "1Y", FIRST_LOAD);
  await expect.poll(async () => Number(await sparkline.getAttribute("data-points"))).toBeGreaterThan(monthPoints * 5);
  await expect(page).toHaveURL(/period=1Y/);

  await page.getByRole("tab", { name: "表格" }).click();
  const table = tw.getByTestId("overview-table");
  await expect(table.locator("tbody tr")).toHaveCount(13); // 1 個指數＋12 家公司
  await expect(table).toContainText("近 1 年");
});

test("點大型股卡片進入看盤頁", async ({ page }) => {
  await page.goto("/overview");
  const first = panel(page, "TW").getByTestId("overview-stock").first();
  await expect(first).toBeVisible(FIRST_LOAD);
  const symbol = (await first.locator("p.font-mono").textContent())!.trim();

  await first.click();
  await expect(page).toHaveURL(new RegExp(`/market\\?symbol=${symbol}`));
  await expect(page.getByTestId("quote-card")).toBeVisible();
});

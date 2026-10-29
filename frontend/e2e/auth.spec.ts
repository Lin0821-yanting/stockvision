import { expect, test } from "@playwright/test";

import { API, PASSWORD, registerUser, uniqueUsername } from "./helpers";

test("從受保護頁面註冊後回到原頁面，登出後再登入", async ({ page }) => {
  const username = uniqueUsername("ui");
  await page.goto("/trading");
  await expect(page.getByText("請先登入")).toBeVisible();

  await page.getByTestId("login-prompt").getByRole("link", { name: "免費註冊" }).click();
  await expect(page).toHaveURL(/\/login\?.*mode=register/);
  const form = page.getByTestId("register-form");
  await form.getByLabel("帳號").fill(username);
  await form.getByLabel("顯示名稱（選填）").fill("測試小明");
  await form.getByLabel("密碼", { exact: true }).fill(PASSWORD);
  await form.getByLabel("確認密碼").fill(PASSWORD);
  await form.getByRole("button", { name: "註冊並登入" }).click();

  await expect(page).toHaveURL(/\/trading$/);
  await expect(page.getByTestId("user-menu")).toContainText("測試小明");
  await expect(page.getByTestId("account-cash")).toHaveText("NT$ 1,000,000");

  await page.getByTestId("user-menu").click();
  await page.getByTestId("logout").click();
  await expect(page.getByText("請先登入")).toBeVisible();
  await expect(page.getByTestId("login-link")).toBeVisible();

  await page.getByTestId("login-prompt").getByRole("link", { name: "登入" }).click();
  const login = page.getByTestId("login-form");
  await login.getByLabel("帳號").fill(username.toUpperCase()); // 帳號不分大小寫
  await login.getByLabel("密碼").fill(PASSWORD);
  await login.getByRole("button", { name: "登入" }).click();

  await expect(page).toHaveURL(/\/trading$/);
  await expect(page.getByTestId("user-menu")).toContainText("測試小明");
});

test("註冊表單會檢查格式與確認密碼", async ({ page }) => {
  await page.goto("/login?mode=register");
  const form = page.getByTestId("register-form");
  await form.getByLabel("帳號").fill("ab");
  await form.getByLabel("密碼", { exact: true }).fill("short");
  await form.getByLabel("確認密碼").fill("different");
  await form.getByRole("button", { name: "註冊並登入" }).click();

  await expect(form).toContainText("帳號需為 3–30 個英文字母、數字或底線");
  await expect(form).toContainText("密碼至少需要 8 個字元");
  await expect(form).toContainText("兩次輸入的密碼不一致");
  await expect(page).toHaveURL(/mode=register/);
});

test("密碼錯誤時顯示提示，不會登入", async ({ page, request }) => {
  // request fixture 有自己的 cookie，不會讓瀏覽器變成已登入
  const { username } = await registerUser(request);
  await page.goto("/login");
  const form = page.getByTestId("login-form");
  await form.getByLabel("帳號").fill(username);
  await form.getByLabel("密碼").fill("wrong-password");
  await form.getByRole("button", { name: "登入" }).click();

  await expect(form.getByRole("alert")).toHaveText("帳號或密碼錯誤");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByTestId("login-link")).toBeVisible();
});

test("未登入時顯示登入提示，不會送出個人資料的請求", async ({ page }) => {
  const personal: string[] = [];
  page.on("request", (request) => {
    if (/\/api\/(portfolio|watchlist|trades|account|alerts|notifications)/.test(request.url())) personal.push(request.url());
  });

  await page.goto("/");
  await expect(page.getByTestId("guest-welcome")).toBeVisible();
  for (const path of ["/portfolio", "/alerts"]) {
    await page.goto(path);
    await expect(page.getByText("請先登入")).toBeVisible();
  }
  await page.goto("/market?symbol=2330");
  const toggle = page.getByTestId("watchlist-toggle");
  await expect(toggle).toHaveText("登入後加入自選");
  await expect(toggle).toHaveAttribute("href", /\/login\?next=%2Fmarket%3Fsymbol%3D2330/);
  await expect(page.getByText("登入後即可使用自選股")).toBeVisible();

  expect(personal).toEqual([]);
});

test("兩個帳號的自選股、交易與資產互相看不到", async ({ page, browser }) => {
  await registerUser(page.request, uniqueUsername("alice"), "Alice");
  await page.request.post(`${API}/api/watchlist`, { data: { symbol: "2330" } });
  await page.request.post(`${API}/api/trades`, { data: { symbol: "2317", side: "BUY", shares: 1 } });
  await page.goto("/");
  await expect(page.getByTestId("watchlist-table")).toContainText("台積電");
  await expect(page.getByTestId("recent-trades")).toContainText("鴻海");

  const other = await browser.newContext();
  try {
    const bobPage = await other.newPage();
    await registerUser(bobPage.request, uniqueUsername("bob"), "Bob");
    await bobPage.goto("/");
    await expect(bobPage.getByTestId("user-menu")).toContainText("Bob");
    await expect(bobPage.getByText("還沒有自選股")).toBeVisible();
    await expect(bobPage.getByText("還沒有交易")).toBeVisible();
    await expect(bobPage.getByTestId("hero-total-assets")).toContainText("NT$ 1,000,000");
  } finally {
    await other.close();
  }
});

import { describe, expect, it } from "vitest";

import { isPersonalKey } from "./use-auth";
import { buildLoginHref } from "./use-login-href";

describe("isPersonalKey", () => {
  it.each([["watchlist"], ["portfolio"], ["alerts"], ["alert-events"], ["notifications"]])("%s 屬於個人資料", (key) => {
    expect(isPersonalKey(key)).toBe(true);
  });

  it("交易紀錄與下單試算的陣列 key 屬於個人資料", () => {
    expect(isPersonalKey(["trades", "current", 5])).toBe(true);
    expect(isPersonalKey(["trade-preview", "2330", "BUY", 1000, 2415])).toBe(true);
  });

  it("公開的行情資料切換帳號時不用清掉", () => {
    expect(isPersonalKey("market-status")).toBe(false);
    expect(isPersonalKey("auth-session")).toBe(false);
    expect(isPersonalKey(["history", "2330", "3M"])).toBe(false);
    expect(isPersonalKey(null)).toBe(false);
  });
});

describe("buildLoginHref", () => {
  it("首頁不帶 next 參數", () => {
    expect(buildLoginHref("login", "/")).toBe("/login");
    expect(buildLoginHref("register", "/")).toBe("/login?mode=register");
  });

  it("記住目前頁面與查詢參數，登入後回來", () => {
    const href = buildLoginHref("login", "/market", "symbol=2330");
    expect(new URL(href, "http://localhost").searchParams.get("next")).toBe("/market?symbol=2330");
  });

  it("在登入頁切換時不會把登入頁當成 next", () => {
    expect(buildLoginHref("register", "/login", "mode=login")).toBe("/login?mode=register");
  });
});

import { describe, expect, it } from "vitest";

import { safeNextPath, validatePassword, validateRegistration, validateUsername } from "./validation";

describe("validateUsername", () => {
  it.each(["alice", "Bob_42", "a_b", "x".repeat(30)])("接受 %s", (value) => {
    expect(validateUsername(value)).toBeNull();
  });

  it.each(["ab", "x".repeat(31), "王小明", "alice!", "a b", ""])("拒絕 %s", (value) => {
    expect(validateUsername(value)).toMatch(/3–30/);
  });
});

describe("validatePassword", () => {
  it("至少 8 個字元、最多 128 個字元", () => {
    expect(validatePassword("1234567")).toMatch(/至少需要 8/);
    expect(validatePassword("12345678")).toBeNull();
    expect(validatePassword("x".repeat(128))).toBeNull();
    expect(validatePassword("x".repeat(129))).toMatch(/最多 128/);
  });
});

describe("validateRegistration", () => {
  it("全部正確時沒有錯誤", () => {
    expect(validateRegistration({ username: "alice", password: "correct-horse", confirm: "correct-horse" })).toEqual({});
  });

  it("逐欄回報錯誤，包含確認密碼不一致", () => {
    expect(validateRegistration({ username: "a", password: "short", confirm: "other" })).toEqual({
      username: expect.stringMatching(/3–30/),
      password: expect.stringMatching(/至少需要 8/),
      confirm: "兩次輸入的密碼不一致",
    });
  });
});

describe("safeNextPath", () => {
  it("保留站內路徑與查詢參數", () => {
    expect(safeNextPath("/trading?symbol=2330")).toBe("/trading?symbol=2330");
    expect(safeNextPath("/alerts")).toBe("/alerts");
  });

  it.each([null, undefined, "", "trading", "https://evil.example", "//evil.example", "/\\evil.example", "/x?u=http://evil"])(
    "不安全或空白的 %s 一律回到首頁",
    (value) => {
      expect(safeNextPath(value)).toBe("/");
    },
  );

  it("不會導回登入頁本身", () => {
    expect(safeNextPath("/login")).toBe("/");
    expect(safeNextPath("/login?mode=register")).toBe("/");
  });
});

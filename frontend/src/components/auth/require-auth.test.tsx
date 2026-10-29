import { render, screen } from "@testing-library/react";
import { SWRConfig } from "swr";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { User } from "@/types/api";

import { RequireAuth } from "./require-auth";

vi.mock("next/navigation", () => ({
  usePathname: () => "/trading",
  useSearchParams: () => new URLSearchParams("symbol=2330"),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const alice: User = {
  id: 1,
  username: "alice",
  display_name: "Alice",
  created_at: "2026-10-29T08:00:00Z",
  last_login_at: "2026-10-29T08:00:00Z",
};

function mockFetch(implementation: (url: string) => Promise<Response>) {
  const fetchMock = vi.fn<typeof fetch>((input) => implementation(String(input)));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderGuarded() {
  return render(
    // 每個測試使用獨立的 SWR 快取
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0, onErrorRetry: () => undefined }}>
      <RequireAuth title="模擬下單" description="每個帳號都有自己的模擬資金">
        <p>下單表單</p>
      </RequireAuth>
    </SWRConfig>,
  );
}

beforeEach(() => {
  vi.unstubAllGlobals();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("RequireAuth", () => {
  it("未登入時顯示登入提示，並記住要回來的頁面", async () => {
    const fetchMock = mockFetch(async () => Response.json({ authenticated: false, user: null }));

    renderGuarded();

    expect(await screen.findByText("請先登入")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "模擬下單" })).toBeInTheDocument();
    expect(screen.queryByText("下單表單")).not.toBeInTheDocument();
    const login = screen.getByRole("link", { name: "登入" });
    expect(new URL(login.getAttribute("href")!, "http://localhost").searchParams.get("next")).toBe("/trading?symbol=2330");
    expect(screen.getByRole("link", { name: "免費註冊" }).getAttribute("href")).toContain("mode=register");
    // 只問過登入狀態，沒有送出任何個人資料的請求
    expect(fetchMock.mock.calls.every(([url]) => String(url).endsWith("/api/auth/session"))).toBe(true);
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ credentials: "include" });
  });

  it("已登入時顯示頁面內容", async () => {
    mockFetch(async () => Response.json({ authenticated: true, user: alice }));

    renderGuarded();

    expect(await screen.findByText("下單表單")).toBeInTheDocument();
    expect(screen.queryByText("請先登入")).not.toBeInTheDocument();
  });

  it("後端沒有啟動時顯示錯誤，而不是要求登入", async () => {
    mockFetch(async () => {
      throw new TypeError("Failed to fetch");
    });

    renderGuarded();

    expect(await screen.findByText("無法確認登入狀態")).toBeInTheDocument();
    expect(screen.queryByText("請先登入")).not.toBeInTheDocument();
  });
});

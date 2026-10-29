import { afterEach, describe, expect, it, vi } from "vitest";

import { API_BASE_URL, ApiError, apiRequest, errorMessage } from "./api-client";

function mockFetch(implementation: () => Promise<Response>) {
  const fetchMock = vi.fn<typeof fetch>(implementation);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function caught(promise: Promise<unknown>): Promise<ApiError> {
  return (await promise.catch((error: unknown) => error)) as ApiError;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("呼叫 Python 後端並帶上查詢參數", async () => {
    const fetchMock = mockFetch(async () => Response.json({ ok: true }));

    const body = await apiRequest<{ ok: boolean }>("/api/stocks/search", { query: { q: "2330", market: undefined } });

    expect(body).toEqual({ ok: true });
    const url = new URL(String(fetchMock.mock.calls[0][0]));
    expect(url.origin + url.pathname).toBe(`${API_BASE_URL}/api/stocks/search`);
    expect(url.searchParams.get("q")).toBe("2330");
    expect(url.searchParams.has("market")).toBe(false);
  });

  it("把後端的錯誤格式轉成 ApiError", async () => {
    mockFetch(async () =>
      Response.json(
        { error: { code: "INSUFFICIENT_FUNDS", message: "可用資金不足", details: { required: "2415000.00" } } },
        { status: 400 },
      ),
    );

    const error = await caught(apiRequest("/api/trades", { method: "POST", json: {} }));

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 400, code: "INSUFFICIENT_FUNDS", message: "可用資金不足" });
    expect(errorMessage(error)).toBe("可用資金不足");
  });

  it("後端沒有啟動時回報網路錯誤", async () => {
    mockFetch(async () => {
      throw new TypeError("Failed to fetch");
    });

    const error = await caught(apiRequest("/api/health"));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.isNetworkError).toBe(true);
    expect(error.message).toContain("無法連線到 StockVision 後端");
  });

  it("非 JSON 的錯誤頁面也有明確訊息", async () => {
    mockFetch(async () => new Response("<html>Bad Gateway</html>", { status: 502 }));

    const error = await caught(apiRequest("/api/portfolio"));

    expect(error).toMatchObject({ status: 502, code: "HTTP_502" });
  });

  it("204 回應沒有內容", async () => {
    mockFetch(async () => new Response(null, { status: 204 }));

    await expect(apiRequest("/api/watchlist/2330", { method: "DELETE" })).resolves.toBeUndefined();
  });
});

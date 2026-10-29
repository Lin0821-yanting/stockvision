import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useStableSlots } from "./use-stable-slots";

describe("useStableSlots", () => {
  it("移除一檔股票時，其他股票保留原本的顏色", () => {
    const { result, rerender } = renderHook(({ items }) => useStableSlots(items, 4), {
      initialProps: { items: ["2330", "2317", "AAPL"] },
    });
    expect(result.current).toEqual({ "2330": 0, "2317": 1, AAPL: 2 });

    rerender({ items: ["2330", "AAPL"] });
    expect(result.current).toEqual({ "2330": 0, AAPL: 2 });

    rerender({ items: ["2330", "AAPL", "NVDA"] });
    expect(result.current).toEqual({ "2330": 0, AAPL: 2, NVDA: 1 });
  });
});

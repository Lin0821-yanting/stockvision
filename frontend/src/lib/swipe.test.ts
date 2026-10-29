import { describe, expect, it } from "vitest";

import { clampPage, dragOffset, swipeDirection, SWIPE_THRESHOLD_PX } from "./swipe";

describe("swipeDirection", () => {
  it("向左滑超過門檻換到下一頁，向右滑回上一頁", () => {
    expect(swipeDirection(-SWIPE_THRESHOLD_PX - 1, 4)).toBe(1);
    expect(swipeDirection(SWIPE_THRESHOLD_PX + 1, -4)).toBe(-1);
  });

  it("距離不足時不換頁", () => {
    expect(swipeDirection(-(SWIPE_THRESHOLD_PX - 1), 0)).toBe(0);
    expect(swipeDirection(30, 0)).toBe(0);
  });

  it("垂直移動比水平多時視為上下捲動", () => {
    expect(swipeDirection(-80, 120)).toBe(0);
    expect(swipeDirection(90, -90)).toBe(0);
  });
});

describe("dragOffset", () => {
  it("中間頁面跟著手指移動", () => {
    expect(dragOffset(-50, 0, 2)).toBe(-50);
    expect(dragOffset(50, 1, 2)).toBe(50);
  });

  it("第一頁往右、最後一頁往左拉時有阻力", () => {
    expect(dragOffset(90, 0, 2)).toBe(30);
    expect(dragOffset(-90, 1, 2)).toBe(-30);
  });
});

describe("clampPage", () => {
  it("不會超出第一頁與最後一頁", () => {
    expect(clampPage(-1, 2)).toBe(0);
    expect(clampPage(2, 2)).toBe(1);
    expect(clampPage(1, 2)).toBe(1);
  });
});

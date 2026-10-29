import { describe, expect, it } from "vitest";

import {
  formatDate,
  formatMarketCap,
  formatMoney,
  formatPercent,
  formatPrice,
  formatSignedMoney,
  formatVolume,
  signedValueClass,
  toneOf,
} from "./format";
import { marketOf } from "./market";

describe("金額格式", () => {
  it("台幣使用 NT$ 與千分位", () => {
    expect(formatMoney(1_000_000)).toBe("NT$ 1,000,000");
    expect(formatMoney(661_944.82)).toBe("NT$ 661,944.82");
    expect(formatMoney(-3500)).toBe("-NT$ 3,500");
  });

  it("美元固定兩位小數", () => {
    expect(formatMoney(343.83, "USD")).toBe("US$ 343.83");
    expect(formatMoney(1719.1, "USD")).toBe("US$ 1,719.10");
  });

  it("損益帶正負號", () => {
    expect(formatSignedMoney(12_000)).toBe("+NT$ 12,000");
    expect(formatSignedMoney(-12_000)).toBe("-NT$ 12,000");
    expect(formatSignedMoney(0)).toBe("NT$ 0");
  });

  it("缺值顯示破折號，不顯示 0", () => {
    expect(formatMoney(null)).toBe("—");
    expect(formatPrice(undefined)).toBe("—");
  });
});

describe("漲跌幅與成交量", () => {
  it("百分比帶正負號", () => {
    expect(formatPercent(1.234)).toBe("+1.23%");
    expect(formatPercent(-0.4124)).toBe("-0.41%");
    expect(formatPercent(5, { signed: false })).toBe("5.00%");
  });

  it("台股成交量以張顯示，美股以股顯示", () => {
    expect(formatVolume(16_828_000, "TW")).toBe("16,828 張");
    expect(formatVolume(34_405_006, "US")).toMatch(/股$/);
  });

  it("日期字串不做時區轉換", () => {
    expect(formatDate("2026-10-29")).toBe("2026/10/29");
  });

  it("市值以兆／億顯示", () => {
    expect(formatMarketCap(62_885_997_412_475, "TWD")).toBe("NT$ 62.89 兆");
    expect(formatMarketCap(225_695_452_260, "TWD")).toBe("NT$ 2,257 億");
    expect(formatMarketCap(5.25235e12, "USD")).toBe("US$ 5.25 兆");
    expect(formatMarketCap(9.5e11, "USD")).toBe("US$ 9,500 億");
    expect(formatMarketCap(null, "USD")).toBe("—");
  });
});

describe("漲跌方向（台股慣例：漲紅跌綠）", () => {
  it("判斷方向", () => {
    expect(toneOf(1)).toBe("up");
    expect(toneOf(-1)).toBe("down");
    expect(toneOf(0)).toBe("flat");
    expect(toneOf(null)).toBe("flat");
  });

  it("正數紅、負數綠", () => {
    expect(signedValueClass(5)).toBe("text-up");
    expect(signedValueClass(-5)).toBe("text-down");
    expect(signedValueClass(0)).toBe("");
  });

  it("依代號判斷市場", () => {
    expect(marketOf("2330")).toBe("TW");
    expect(marketOf("00400A")).toBe("TW");
    expect(marketOf("AAPL")).toBe("US");
  });
});

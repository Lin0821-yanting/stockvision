import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ErrorState } from "@/components/common/states";
import { ApiError } from "@/services/api-client";
import type { Quote } from "@/types/api";

import { DataSourceBadge } from "./data-source-badge";
import { PriceChange } from "./price-change";

const quote: Quote = {
  symbol: "2330",
  market: "TW",
  name: "台積電",
  exchange: "TWSE",
  currency: "TWD",
  price: 2415,
  change: -10,
  change_pct: -0.4124,
  open: 2420,
  high: 2425,
  low: 2390,
  prev_close: 2425,
  volume: 16_828_000,
  volume_note: null,
  trade_date: "2026-10-29",
  as_of: "2026-10-29T13:30:00+08:00",
  kind: "close",
  source: "TWSE MIS",
  note: "今日收盤（TWSE MIS）",
  market_open: false,
  fetched_at: "2026-10-29T10:42:27Z",
};

describe("PriceChange", () => {
  it("上漲顯示紅色、▲ 與正號", () => {
    render(<PriceChange change={10} changePct={0.41} />);

    const element = screen.getByText("+10.00").parentElement!;
    expect(element).toHaveClass("text-up");
    expect(element).toHaveTextContent("▲");
    expect(screen.getByText("上漲")).toBeInTheDocument();
  });

  it("下跌顯示綠色與 ▼", () => {
    render(<PriceChange change={-10} changePct={-0.41} />);

    const element = screen.getByText("-10.00").parentElement!;
    expect(element).toHaveClass("text-down");
    expect(element).toHaveTextContent("▼");
    expect(element).toHaveTextContent("(-0.41%)");
  });

  it("沒有資料時顯示破折號", () => {
    render(<PriceChange change={null} changePct={null} />);

    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("DataSourceBadge", () => {
  it("收盤資料標示來源、資料日期與說明，不會標成盤中", () => {
    render(<DataSourceBadge quote={quote} />);

    expect(screen.getByText("收盤")).toBeInTheDocument();
    expect(screen.queryByText("盤中")).not.toBeInTheDocument();
    expect(screen.getByText("來源：TWSE MIS")).toBeInTheDocument();
    expect(screen.getByText(/資料日期 2026\/10\/29/)).toBeInTheDocument();
    expect(screen.getByText("今日收盤（TWSE MIS）")).toBeInTheDocument();
  });

  it("盤中報價顯示盤中標籤", () => {
    render(<DataSourceBadge quote={{ ...quote, kind: "realtime", note: null }} />);

    expect(screen.getByText("盤中")).toBeInTheDocument();
  });
});

describe("ErrorState", () => {
  it("顯示後端錯誤訊息與代碼，並可以重試", async () => {
    const onRetry = vi.fn();
    const error = new ApiError({ status: 503, code: "UPSTREAM_UNAVAILABLE", message: "無法從 FinMind 取得資料：連線逾時" });
    render(<ErrorState error={error} onRetry={onRetry} />);

    expect(screen.getByRole("alert")).toHaveTextContent("無法從 FinMind 取得資料：連線逾時");
    expect(screen.getByText("錯誤代碼：UPSTREAM_UNAVAILABLE")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "重新載入" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});

"use client";

import { TriangleAlert } from "lucide-react";

import { ErrorState } from "@/components/common/states";
import { useOverview } from "@/hooks/use-market";
import { formatDate, formatTime } from "@/lib/format";
import { MARKET_LABEL } from "@/lib/market";
import { cn } from "@/lib/utils";
import type { Market, Period } from "@/types/api";

import { IndexCard, OverviewSkeleton, StockCard } from "./overview-cards";
import { OverviewTable } from "./overview-table";

export type OverviewView = "cards" | "table";

const INDEX_COUNT: Record<Market, number> = { TW: 1, US: 3 };

/** 一個市場的頁面：上方指數，下方市值前幾大公司（卡片或表格） */
export function MarketPanel({
  market,
  period,
  view,
  enabled,
}: {
  market: Market;
  period: Period;
  view: OverviewView;
  enabled: boolean;
}) {
  const { data, error, mutate } = useOverview(market, period, enabled);

  if (!data) {
    if (error) return <ErrorState error={error} title={`無法取得${MARKET_LABEL[market]}大盤資料`} onRetry={() => mutate()} />;
    return <OverviewSkeleton indices={INDEX_COUNT[market]} />;
  }

  // 切換期間時保留上一份資料並降低透明度，新資料到了才換掉
  const switching = data.period !== period;
  const singleIndex = data.indices.length === 1;

  return (
    <div
      className={cn("space-y-4 transition-opacity duration-300", switching && "opacity-60")}
      data-testid={`overview-${market}`}
      data-period={data.period}
    >
      {data.warnings.map((warning) => (
        <p key={warning} role="status" className="flex items-start gap-2 rounded-lg border border-dashed px-3 py-2 text-sm text-muted-foreground">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          {warning}
        </p>
      ))}
      {error ? <p className="text-xs text-destructive">最新一次更新失敗，顯示上一次取得的資料</p> : null}

      {view === "cards" ? (
        <>
          <div className={cn("grid gap-3", !singleIndex && "sm:grid-cols-3")}>
            {data.indices.map((item) => (
              <IndexCard key={item.symbol} item={item} market={market} period={data.period} wide={singleIndex} />
            ))}
          </div>
          <div className="flex flex-wrap items-baseline justify-between gap-x-3">
            <h2 className="text-base font-semibold">市值前 {data.stocks.length} 大公司</h2>
            <p className="text-xs text-muted-foreground">更新於 {formatTime(data.fetched_at)}（台北時間）</p>
          </div>
          {data.stocks.length ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {data.stocks.map((item) => (
                <StockCard key={item.symbol} item={item} period={data.period} />
              ))}
            </div>
          ) : null}
        </>
      ) : (
        <>
          <p className="text-right text-xs text-muted-foreground">更新於 {formatTime(data.fetched_at)}（台北時間）</p>
          <OverviewTable data={data} />
        </>
      )}

      <footer className="space-y-1 text-xs leading-relaxed text-muted-foreground">
        {data.ranking ? (
          <p>
            排行依據：{data.ranking.method}（{data.ranking.source}，資料日期 {formatDate(data.ranking.as_of)}）。{data.ranking.note}。
          </p>
        ) : null}
        <p>
          {data.data_note}。每張走勢圖使用各自的價格刻度，走勢來源 {data.history_source}。
        </p>
      </footer>
    </div>
  );
}

"use client";

import Link from "next/link";

import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { PriceChange } from "@/components/stock/price-change";
import { Skeleton } from "@/components/ui/skeleton";
import {
  formatDateTime,
  formatMarketCap,
  formatPercent,
  formatPrice,
  toneOf,
  TONE_ARROW,
  TONE_LABEL,
  TONE_TEXT_CLASS,
} from "@/lib/format";
import { MARKET_TIMEZONE } from "@/lib/market";
import { cn } from "@/lib/utils";
import type { Market, OverviewItem, Period } from "@/types/api";

import { Sparkline } from "./sparkline";

export const PERIOD_LABEL: Record<Period, string> = { "1M": "近 1 個月", "3M": "近 3 個月", "6M": "近 6 個月", "1Y": "近 1 年" };

export function PeriodReturn({ value, className }: { value: number | null; className?: string }) {
  const tone = toneOf(value);
  if (value == null) return <span className={cn("text-muted-foreground", className)}>—</span>;
  return (
    <span className={cn("tabular whitespace-nowrap", TONE_TEXT_CLASS[tone], className)}>
      <span aria-hidden>{TONE_ARROW[tone]} </span>
      <span className="sr-only">{TONE_LABEL[tone]}</span>
      {formatPercent(value)}
    </span>
  );
}

function trendLabel(item: OverviewItem, period: Period): string {
  const first = item.points[0]?.close;
  const last = item.points.at(-1)?.close;
  return `${item.name} ${PERIOD_LABEL[period]}每日收盤走勢：${formatPrice(first)} 到 ${formatPrice(last)}，報酬 ${formatPercent(item.period_return_pct)}`;
}

function QuoteSource({ item, market }: { item: OverviewItem; market: Market }) {
  if (!item.quote) return <span className="text-destructive">{item.quote_error?.message ?? "報價暫時無法取得"}</span>;
  return (
    <span className="truncate" title={item.quote.note ?? undefined}>
      {item.quote.source}・{formatDateTime(item.quote.as_of, MARKET_TIMEZONE[market])}
    </span>
  );
}

function Trend({ item, period, className }: { item: OverviewItem; period: Period; className: string }) {
  if (item.history_error) {
    return (
      <div className={cn("flex items-center justify-center rounded-md bg-muted/30 px-2 text-center text-xs text-muted-foreground", className)}>
        走勢暫時無法取得
      </div>
    );
  }
  return <Sparkline points={item.points} label={trendLabel(item, period)} className={className} />;
}

/** 指數卡：只有一個指數（台股）時橫跨整列，走勢圖放大 */
export function IndexCard({ item, market, period, wide = false }: { item: OverviewItem; market: Market; period: Period; wide?: boolean }) {
  const quote = item.quote;
  return (
    <section
      className={cn("rounded-xl border bg-card p-4", wide && "sm:grid sm:grid-cols-[minmax(0,15rem)_minmax(0,1fr)] sm:items-center sm:gap-6")}
      aria-label={item.name}
      data-testid="overview-index"
    >
      <div className="min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="truncate text-sm font-medium">{item.name}</h3>
            <p className="font-mono text-xs text-muted-foreground">{item.symbol}</p>
          </div>
          {quote ? <QuoteKindBadge kind={quote.kind} /> : null}
        </div>
        <p className="mt-2 text-2xl font-semibold tracking-tight tabular">{formatPrice(quote?.price)}</p>
        {quote ? <PriceChange change={quote.change} changePct={quote.change_pct} className="text-sm" /> : null}
        <p className="mt-2 flex min-w-0 flex-col gap-0.5 text-xs text-muted-foreground">
          <span>
            {PERIOD_LABEL[period]} <PeriodReturn value={item.period_return_pct} />
          </span>
          <QuoteSource item={item} market={market} />
        </p>
      </div>
      <Trend item={item} period={period} className={wide ? "mt-3 h-28 sm:mt-0 sm:h-32" : "mt-3 h-16 sm:h-20"} />
    </section>
  );
}

/** 大型股卡片：點選進入看盤頁 */
export function StockCard({ item, period }: { item: OverviewItem; period: Period }) {
  const quote = item.quote;
  return (
    <Link
      href={`/market?symbol=${encodeURIComponent(item.symbol)}`}
      draggable={false}
      className="flex min-w-0 flex-col gap-2 rounded-xl border bg-card p-3 transition-colors outline-none hover:border-primary/50 hover:bg-accent/30 focus-visible:ring-[3px] focus-visible:ring-ring/50"
      data-testid="overview-stock"
    >
      <div className="flex items-start gap-2">
        <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground tabular">#{item.rank}</span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{item.name}</p>
          <p className="font-mono text-xs text-muted-foreground">{item.symbol}</p>
        </div>
        {quote ? <QuoteKindBadge kind={quote.kind} className="hidden px-1.5 py-0 text-[10px] sm:inline-flex" /> : null}
      </div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-2">
        <span className="text-lg font-semibold tabular">{formatPrice(quote?.price)}</span>
        {quote ? <PriceChange change={quote.change} changePct={quote.change_pct} hideAmount className="text-xs" /> : null}
      </div>
      <Trend item={item} period={period} className="h-14" />
      <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
        <span className="whitespace-nowrap">市值 {formatMarketCap(item.market_cap, item.currency)}</span>
        <PeriodReturn value={item.period_return_pct} />
      </div>
      {!quote ? <p className="text-xs text-destructive">{item.quote_error?.message ?? "報價暫時無法取得"}</p> : null}
    </Link>
  );
}

export function OverviewSkeleton({ indices }: { indices: number }) {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="載入中">
      <div className={cn("grid gap-3", indices > 1 && "sm:grid-cols-3")}>
        {Array.from({ length: indices }, (_, index) => (
          <Skeleton key={index} className="h-36 rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 12 }, (_, index) => (
          <Skeleton key={index} className="h-40 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

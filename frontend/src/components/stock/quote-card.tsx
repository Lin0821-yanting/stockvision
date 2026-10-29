"use client";

import Link from "next/link";
import { ArrowLeftRight, BellPlus, GitCompareArrows, TrendingDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { usePriceFlash } from "@/hooks/use-price-flash";
import { formatPrice, formatVolume } from "@/lib/format";
import { MARKET_LABEL, exchangeLabel } from "@/lib/market";
import { cn } from "@/lib/utils";
import type { StockDetail } from "@/types/api";

import { DataSourceBadge } from "./data-source-badge";
import { PriceChange } from "./price-change";
import { WatchlistToggle } from "./watchlist-toggle";

function Stat({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-muted/40 px-3 py-2" title={hint}>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 truncate text-sm font-medium tabular">{value}</dd>
    </div>
  );
}

export function QuoteCard({ detail }: { detail: StockDetail }) {
  const { stock, quote } = detail;
  const flash = usePriceFlash(quote.price);

  return (
    <Card data-testid="quote-card">
      <CardHeader className="gap-3 sm:grid-cols-[1fr_auto]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold">{stock.name}</h2>
            <span className="font-mono text-muted-foreground">{stock.symbol}</span>
            <Badge variant="secondary">{MARKET_LABEL[stock.market]}</Badge>
            {stock.market === "TW" ? <Badge variant="outline">{exchangeLabel(stock.exchange)}</Badge> : null}
            {stock.industry ? <span className="truncate text-xs text-muted-foreground">{stock.industry}</span> : null}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 sm:justify-end">
          <WatchlistToggle symbol={stock.symbol} />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end gap-x-4 gap-y-1">
          <div
            key={flash.key}
            data-testid="quote-price"
            className={cn(
              "-mx-1 rounded-md px-1 text-4xl font-semibold tracking-tight motion-reduce:animate-none",
              flash.direction === "up" && "animate-flash-up",
              flash.direction === "down" && "animate-flash-down",
            )}
          >
            {quote.price != null ? formatPrice(quote.price) : "尚無成交"}
          </div>
          <span className="pb-1 text-sm text-muted-foreground">{stock.currency}</span>
          <PriceChange change={quote.change} changePct={quote.change_pct} className="pb-1 text-lg" />
          {detail.is_20d_low ? (
            <Badge variant="outline" className="mb-1.5 border-down/40 text-down" data-testid="new-low-badge">
              <TrendingDown />
              創 20 日新低
            </Badge>
          ) : null}
        </div>

        <DataSourceBadge quote={quote} />

        <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
          <Stat label="開盤" value={formatPrice(quote.open)} />
          <Stat label="最高" value={formatPrice(quote.high)} />
          <Stat label="最低" value={formatPrice(quote.low)} />
          <Stat label="昨收" value={formatPrice(quote.prev_close)} />
          <Stat label="成交量" value={formatVolume(quote.volume, stock.market)} hint={quote.volume_note ?? undefined} />
          <Stat
            label="20 日最低收盤"
            value={formatPrice(detail.low_20d)}
            hint="前 20 個交易日（不含報價當日）的最低收盤價，由 Python Pandas 計算"
          />
        </dl>
        {quote.volume_note ? <p className="text-xs text-muted-foreground">{quote.volume_note}</p> : null}

        <div className="flex flex-wrap gap-2">
          <Button asChild size="sm">
            <Link href={`/trading?symbol=${stock.symbol}`}>
              <ArrowLeftRight />
              模擬下單
            </Link>
          </Button>
          <Button asChild size="sm" variant="outline">
            <Link href={`/alerts?symbol=${stock.symbol}`}>
              <BellPlus />
              設定提醒
            </Link>
          </Button>
          <Button asChild size="sm" variant="outline">
            <Link href={`/compare?symbols=${stock.symbol}`}>
              <GitCompareArrows />
              加入比較
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

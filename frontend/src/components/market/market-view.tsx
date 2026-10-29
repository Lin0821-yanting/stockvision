"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { CardSkeleton, ErrorState } from "@/components/common/states";
import { MarketStatusPills } from "@/components/layout/market-status-pills";
import { HistoryTable } from "@/components/stock/history-table";
import { PriceHistoryChart } from "@/components/stock/price-history-chart";
import { QuoteCard } from "@/components/stock/quote-card";
import { StockSearch } from "@/components/stock/stock-search";
import { WatchlistPanel } from "@/components/stock/watchlist-panel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useHistory, useStockDetail } from "@/hooks/use-market";
import { formatDate, formatPercent, formatPrice, formatVolume, toneOf, TONE_ARROW, TONE_TEXT_CLASS } from "@/lib/format";
import { POPULAR_SYMBOLS } from "@/lib/market";
import { cn } from "@/lib/utils";
import { errorMessage } from "@/services/api-client";
import type { Period } from "@/types/api";

const PERIODS: { value: Period; label: string }[] = [
  { value: "1M", label: "1 個月" },
  { value: "3M", label: "3 個月" },
  { value: "6M", label: "6 個月" },
  { value: "1Y", label: "1 年" },
];

function HistorySection({ symbol }: { symbol: string }) {
  const [period, setPeriod] = useState<Period>("3M");
  const history = useHistory(symbol, period);
  const data = history.data;
  // 切換期間時保留上一張圖（降低透明度），不閃爍骨架
  const switching = Boolean(data && (data.period !== period || history.isValidating));
  const stats = data?.stats;
  const tone = toneOf(stats?.period_return_pct);

  const [view, setView] = useState<"chart" | "table">("chart");

  return (
    <Card className="gap-4">
      <CardHeader>
        <CardTitle>歷史走勢</CardTitle>
        <CardDescription>
          {data ? `${data.data_note}・來源 ${data.source}` : "每日收盤資料（非即時報價）"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 篩選列：期間與顯示方式放在同一列，作用於下方所有內容 */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Tabs value={period} onValueChange={(value) => setPeriod(value as Period)}>
            <TabsList aria-label="走勢期間">
              {PERIODS.map((item) => (
                <TabsTrigger key={item.value} value={item.value} className="px-2.5">
                  {item.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <Tabs value={view} onValueChange={(value) => setView(value as "chart" | "table")}>
            <TabsList aria-label="顯示方式">
              <TabsTrigger value="chart">走勢圖</TabsTrigger>
              <TabsTrigger value="table">資料表</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        {history.error && !data ? (
          <ErrorState error={history.error} onRetry={() => history.mutate()} />
        ) : !data ? (
          <Skeleton className="h-80 w-full" />
        ) : (
          <>
            <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4" data-testid="history-stats">
              <div className="rounded-lg bg-muted/40 px-3 py-2">
                <dt className="text-xs text-muted-foreground">區間報酬率</dt>
                <dd className={cn("mt-0.5 font-semibold tabular", TONE_TEXT_CLASS[tone])}>
                  {TONE_ARROW[tone]} {formatPercent(stats?.period_return_pct)}
                </dd>
              </div>
              <div className="rounded-lg bg-muted/40 px-3 py-2">
                <dt className="text-xs text-muted-foreground">區間最高／最低</dt>
                <dd className="mt-0.5 font-medium tabular">
                  {formatPrice(stats?.high)} / {formatPrice(stats?.low)}
                </dd>
              </div>
              <div className="rounded-lg bg-muted/40 px-3 py-2">
                <dt className="text-xs text-muted-foreground">平均成交量</dt>
                <dd className="mt-0.5 font-medium tabular">{formatVolume(stats?.avg_volume, data.market)}</dd>
              </div>
              <div className="rounded-lg bg-muted/40 px-3 py-2">
                <dt className="text-xs text-muted-foreground">資料區間（{stats?.trading_days ?? 0} 個交易日）</dt>
                <dd className="mt-0.5 font-medium tabular">
                  {formatDate(stats?.start_date)}–{formatDate(stats?.end_date).slice(5)}
                </dd>
              </div>
            </dl>
            {history.error ? (
              <p className="text-xs text-destructive">最新一次更新失敗：{errorMessage(history.error)}</p>
            ) : null}
            {view === "chart" ? <PriceHistoryChart history={data} dimmed={switching} /> : <HistoryTable history={data} />}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function StockOverview({ symbol }: { symbol: string }) {
  const detail = useStockDetail(symbol);

  if (detail.error && !detail.data) {
    return <ErrorState error={detail.error} title={`無法取得 ${symbol} 的資料`} onRetry={() => detail.mutate()} />;
  }
  if (!detail.data) return <CardSkeleton rows={6} />;

  return (
    <div className="space-y-2">
      <QuoteCard detail={detail.data} />
      {detail.error ? (
        <p className="text-xs text-destructive" role="status">
          報價更新失敗（顯示上一次取得的資料）：{errorMessage(detail.error)}
        </p>
      ) : null}
    </div>
  );
}

function Welcome({ onPick }: { onPick: (symbol: string) => void }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>從熱門股票開始</CardTitle>
        <CardDescription>台股盤中報價來自證交所 MIS（約 5 秒更新）；美股需設定 Finnhub API Key 才有盤中報價，否則顯示最近收盤。</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {POPULAR_SYMBOLS.map((item) => (
          <Button key={item.symbol} variant="outline" size="sm" onClick={() => onPick(item.symbol)}>
            <span className="font-mono">{item.symbol}</span>
            <span className="text-muted-foreground">{item.name}</span>
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}

export function MarketView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const symbol = searchParams.get("symbol")?.trim().toUpperCase() || null;
  const select = (value: string) => router.push(`/market?symbol=${encodeURIComponent(value)}`);

  return (
    <>
      <PageHeader
        title="股票看盤"
        description="搜尋台股與美股，查看盤中報價、收盤資料與歷史走勢"
        actions={<MarketStatusPills />}
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="min-w-0 space-y-6">
          <StockSearch onSelect={(stock) => select(stock.symbol)} autoFocus={!symbol} />
          {symbol ? (
            <>
              <StockOverview key={symbol} symbol={symbol} />
              <HistorySection key={`history-${symbol}`} symbol={symbol} />
            </>
          ) : (
            <Welcome onPick={select} />
          )}
        </div>
        <aside className="min-w-0">
          <WatchlistPanel activeSymbol={symbol} />
        </aside>
      </div>
    </>
  );
}

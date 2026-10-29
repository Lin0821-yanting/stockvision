"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Calculator, GitCompareArrows, X } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { CardSkeleton, EmptyState, ErrorState } from "@/components/common/states";
import { StockSearch } from "@/components/stock/stock-search";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCompare } from "@/hooks/use-market";
import { useStableSlots } from "@/hooks/use-stable-slots";
import { formatDate, formatPercent, signedValueClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import { errorMessage } from "@/services/api-client";
import type { Period } from "@/types/api";

import { CompareChart, type SeriesMeta } from "./compare-chart";
import { CompareTable, NormalizedTable } from "./compare-table";
import { PriceMultiples } from "./price-multiples";

const MAX = 4;
const SLOT_COLORS = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"];
const PERIODS: { value: Period; label: string }[] = [
  { value: "1M", label: "1 個月" },
  { value: "3M", label: "3 個月" },
  { value: "6M", label: "6 個月" },
  { value: "1Y", label: "1 年" },
];
const SUGGESTIONS = [
  { label: "台積電 vs 鴻海", symbols: ["2330", "2317"] },
  { label: "台積電 vs NVIDIA", symbols: ["2330", "NVDA"] },
  { label: "台積電、聯發科、鴻海", symbols: ["2330", "2454", "2317"] },
  { label: "Apple、Microsoft、NVIDIA", symbols: ["AAPL", "MSFT", "NVDA"] },
];

function parseSymbols(raw: string | null): string[] {
  const items = (raw ?? "")
    .split(",")
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
  return Array.from(new Set(items)).slice(0, MAX);
}

function parsePeriod(raw: string | null): Period {
  return PERIODS.some((item) => item.value === raw) ? (raw as Period) : "3M";
}

export function CompareView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const symbols = parseSymbols(searchParams.get("symbols"));
  const period = parsePeriod(searchParams.get("period"));
  const slots = useStableSlots(symbols, MAX);
  const compare = useCompare(symbols, period);
  const [view, setView] = useState<"chart" | "table">("chart");

  const colorOf = (symbol: string) => SLOT_COLORS[slots[symbol] ?? 0];
  const update = (next: string[], nextPeriod: Period = period) => {
    const query = new URLSearchParams({ period: nextPeriod });
    if (next.length) query.set("symbols", next.join(","));
    router.replace(`/compare?${query.toString()}`);
  };
  const add = (symbol: string) => {
    if (!symbols.includes(symbol) && symbols.length < MAX) update([...symbols, symbol]);
  };

  const data = compare.data;
  const current = data && data.symbols.join(",") === symbols.join(",") && data.period === period;
  const names = Object.fromEntries((data?.stocks ?? []).map((stock) => [stock.symbol, stock.name]));
  const series: SeriesMeta[] = (data?.stocks ?? []).map((stock) => ({
    symbol: stock.symbol,
    name: stock.name,
    color: colorOf(stock.symbol),
  }));

  return (
    <>
      <PageHeader title="股票比較" description="選擇 2 至 4 檔股票（台股、美股都可以），比較標準化走勢與區間報酬" />
      <div className="space-y-6">
        <Card className="gap-4">
          <CardHeader>
            <CardTitle>比較對象與期間</CardTitle>
            <CardDescription>顏色固定跟著股票，移除其中一檔不會讓其他股票換色</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-2" data-testid="compare-symbols">
              {symbols.map((symbol) => (
                <span key={symbol} className="inline-flex items-center gap-2 rounded-full border py-1 pr-1 pl-3 text-sm">
                  <span className="inline-block h-0.5 w-3 rounded" style={{ backgroundColor: colorOf(symbol) }} aria-hidden />
                  <span className="font-mono">{symbol}</span>
                  {names[symbol] ? <span className="text-muted-foreground">{names[symbol]}</span> : null}
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    className="size-6 rounded-full"
                    onClick={() => update(symbols.filter((item) => item !== symbol))}
                    aria-label={`移除 ${symbol}`}
                  >
                    <X />
                  </Button>
                </span>
              ))}
              {symbols.length < MAX ? (
                <StockSearch
                  className="w-full sm:w-72"
                  placeholder={symbols.length ? "再加入一檔股票" : "加入第一檔股票"}
                  onSelect={(stock) => add(stock.symbol)}
                />
              ) : (
                <span className="text-xs text-muted-foreground">最多比較 {MAX} 檔</span>
              )}
            </div>
            <Tabs value={period} onValueChange={(value) => update(symbols, value as Period)}>
              <TabsList aria-label="比較期間">
                {PERIODS.map((item) => (
                  <TabsTrigger key={item.value} value={item.value} className="px-2.5">
                    {item.label}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
          </CardContent>
        </Card>

        {symbols.length < 2 ? (
          <EmptyState
            icon={GitCompareArrows}
            title="至少選擇 2 檔股票"
            description="可以直接套用下面的組合，或用上方搜尋框加入股票"
            action={
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((item) => (
                  <Button key={item.label} variant="outline" size="sm" onClick={() => update(item.symbols)}>
                    {item.label}
                  </Button>
                ))}
              </div>
            }
          />
        ) : compare.error && !data ? (
          <ErrorState error={compare.error} title="比較資料載入失敗" onRetry={() => compare.mutate()} />
        ) : !data ? (
          <CardSkeleton rows={8} />
        ) : (
          <>
            <div className="flex gap-3 rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm" data-testid="compare-method">
              <Calculator className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
              <p>
                由 <strong>{data.computed_by}</strong> 計算：{data.method}。共同區間 {formatDate(data.common_start)}–
                {formatDate(data.common_end)}，共 {data.aligned_points} 個交易日。
              </p>
            </div>
            {compare.error ? <p className="text-xs text-destructive">最新一次更新失敗：{errorMessage(compare.error)}</p> : null}

            <Card className="gap-4">
              <CardHeader>
                <CardTitle>標準化走勢（共同起始日 = 100）</CardTitle>
                <CardDescription>指數高於 100 代表比起始日上漲；同一條基準線方便比較不同價位與幣別的股票</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm" aria-label="圖例" data-testid="compare-legend">
                    {data.stocks.map((stock) => (
                      <li key={stock.symbol} className="flex items-center gap-2">
                        <span className="inline-block h-0.5 w-4 rounded" style={{ backgroundColor: colorOf(stock.symbol) }} aria-hidden />
                        <span>
                          {stock.name} <span className="font-mono text-muted-foreground">{stock.symbol}</span>
                        </span>
                        <span className={cn("font-medium tabular", signedValueClass(stock.cumulative_return_pct))}>
                          {formatPercent(stock.cumulative_return_pct)}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <Tabs value={view} onValueChange={(value) => setView(value as "chart" | "table")}>
                    <TabsList aria-label="顯示方式">
                      <TabsTrigger value="chart">走勢圖</TabsTrigger>
                      <TabsTrigger value="table">資料表</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
                {view === "chart" ? (
                  <CompareChart data={data.series} series={series} dimmed={!current || compare.isValidating} />
                ) : (
                  <NormalizedTable data={data.series} stocks={data.stocks} />
                )}
              </CardContent>
            </Card>

            <Card className="gap-4">
              <CardHeader>
                <CardTitle>各股收盤價</CardTitle>
                <CardDescription>每檔股票用自己的價格軸與幣別（small multiples），不把不同價位放在同一張雙軸圖上</CardDescription>
              </CardHeader>
              <CardContent>
                <PriceMultiples data={data.series} stocks={data.stocks} colorOf={colorOf} />
              </CardContent>
            </Card>

            <Card className="gap-4">
              <CardHeader>
                <CardTitle>比較表</CardTitle>
                <CardDescription>最新價格為盤中或最近收盤（見標籤）；累積報酬與最大回檔以共同交易日計算</CardDescription>
              </CardHeader>
              <CardContent>
                <CompareTable stocks={data.stocks} colorOf={colorOf} />
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </>
  );
}

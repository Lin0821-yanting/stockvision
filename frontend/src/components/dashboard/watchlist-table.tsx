"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeftRight, GitCompareArrows, Plus, Star, Trash } from "lucide-react";

import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/states";
import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { PriceChange } from "@/components/stock/price-change";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useWatchlist } from "@/hooks/use-watchlist";
import { formatPrice, formatTime, formatVolume } from "@/lib/format";
import { MARKET_TIMEZONE, POPULAR_SYMBOLS } from "@/lib/market";

export function WatchlistCard() {
  const router = useRouter();
  const { data, error, isLoading, mutate, add, remove } = useWatchlist();
  const [selected, setSelected] = useState<string[]>([]);
  const items = data?.items ?? [];
  const chosen = selected.filter((symbol) => items.some((item) => item.symbol === symbol));

  function toggle(symbol: string, checked: boolean) {
    setSelected((current) => (checked ? [...current, symbol].slice(-4) : current.filter((item) => item !== symbol)));
  }

  return (
    <Card className="min-w-0 gap-4">
      <CardHeader>
        <CardTitle>自選股</CardTitle>
        <CardDescription>勾選 2–4 檔可直接比較；交易時段每 10 秒自動更新</CardDescription>
        <CardAction>
          <Button
            size="sm"
            variant="outline"
            disabled={chosen.length < 2}
            onClick={() => router.push(`/compare?symbols=${chosen.join(",")}&period=3M`)}
            data-testid="compare-selected"
          >
            <GitCompareArrows />
            比較（{chosen.length}）
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : isLoading && !data ? (
          <TableSkeleton rows={4} />
        ) : !items.length ? (
          <EmptyState
            icon={Star}
            title="還沒有自選股"
            description="點下面的股票直接加入，或到股票看盤頁搜尋"
            action={
              <div className="flex flex-wrap justify-center gap-2">
                {POPULAR_SYMBOLS.slice(0, 6).map((item) => (
                  <Button key={item.symbol} variant="outline" size="sm" onClick={() => add(item.symbol)}>
                    <Plus />
                    {item.symbol} {item.name}
                  </Button>
                ))}
              </div>
            }
          />
        ) : (
          <Table data-testid="watchlist-table">
            <TableHeader>
              <TableRow>
                <TableHead className="w-8">
                  <span className="sr-only">選取比較</span>
                </TableHead>
                <TableHead>股票</TableHead>
                <TableHead className="text-right">價格</TableHead>
                <TableHead className="text-right">漲跌</TableHead>
                <TableHead className="hidden text-right 2xl:table-cell">成交量</TableHead>
                <TableHead>資料</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody className="tabular">
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <Checkbox
                      checked={chosen.includes(item.symbol)}
                      onCheckedChange={(checked) => toggle(item.symbol, checked === true)}
                      aria-label={`選取 ${item.name} 進行比較`}
                    />
                  </TableCell>
                  <TableCell>
                    <Link href={`/market?symbol=${item.symbol}`} className="hover:underline">
                      <span className="font-medium">{item.name}</span>
                      <span className="ml-1.5 font-mono text-xs text-muted-foreground">{item.symbol}</span>
                    </Link>
                  </TableCell>
                  {item.quote ? (
                    <>
                      <TableCell className="text-right font-medium">
                        {formatPrice(item.quote.price)}
                        <span className="ml-1 text-xs text-muted-foreground">{item.currency}</span>
                      </TableCell>
                      <TableCell className="text-right">
                        <PriceChange change={item.quote.change} changePct={item.quote.change_pct} />
                      </TableCell>
                      <TableCell className="hidden text-right text-muted-foreground 2xl:table-cell">
                        {formatVolume(item.quote.volume, item.market)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <QuoteKindBadge kind={item.quote.kind} className="px-1.5 py-0 text-[10px]" />
                          {formatTime(item.quote.as_of, MARKET_TIMEZONE[item.market]).slice(0, 5)}
                        </div>
                      </TableCell>
                    </>
                  ) : (
                    <TableCell colSpan={4} className="text-xs text-destructive">
                      {item.quote_error?.message ?? "報價暫時無法取得"}
                    </TableCell>
                  )}
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button asChild size="icon-sm" variant="ghost">
                        <Link href={`/trading?symbol=${item.symbol}`} aria-label={`模擬下單 ${item.name}`} title="模擬下單">
                          <ArrowLeftRight />
                        </Link>
                      </Button>
                      <Button variant="ghost" size="icon-sm" onClick={() => remove(item.symbol)} aria-label={`從自選股移除 ${item.name}`}>
                        <Trash />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

"use client";

import Link from "next/link";
import { Star } from "lucide-react";

import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/states";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useWatchlist } from "@/hooks/use-watchlist";
import { formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";

import { QuoteKindBadge } from "./data-source-badge";
import { PriceChange } from "./price-change";

/** 精簡版自選股清單（看盤頁側欄），點選即可切換股票 */
export function WatchlistPanel({ activeSymbol }: { activeSymbol?: string | null }) {
  const { data, error, isLoading, mutate } = useWatchlist();

  return (
    <Card className="gap-4">
      <CardHeader>
        <CardTitle>我的自選股</CardTitle>
        <CardDescription>資料保存在本機 SQLite，盤中每 10 秒更新</CardDescription>
      </CardHeader>
      <CardContent>
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : isLoading && !data ? (
          <TableSkeleton rows={4} />
        ) : !data?.items.length ? (
          <EmptyState icon={Star} title="尚未加入自選股" description="在股票資訊卡按「加入自選」即可追蹤" className="p-6" />
        ) : (
          <ul className="-mx-2 divide-y divide-border" data-testid="watchlist-panel">
            {data.items.map((item) => (
              <li key={item.id}>
                <Link
                  href={`/market?symbol=${item.symbol}`}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-2 py-2.5 transition-colors hover:bg-accent/60",
                    activeSymbol === item.symbol && "bg-accent",
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{item.name}</p>
                    <p className="font-mono text-xs text-muted-foreground">{item.symbol}</p>
                  </div>
                  {item.quote ? (
                    <div className="text-right">
                      <p className="text-sm font-medium tabular">{formatPrice(item.quote.price)}</p>
                      <PriceChange change={item.quote.change} changePct={item.quote.change_pct} hideAmount className="text-xs" />
                    </div>
                  ) : (
                    <span className="text-xs text-destructive">{item.quote_error?.message ?? "報價無法取得"}</span>
                  )}
                  {item.quote ? <QuoteKindBadge kind={item.quote.kind} className="hidden sm:inline-flex" /> : null}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

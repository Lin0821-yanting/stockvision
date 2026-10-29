"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { CardSkeleton, EmptyState, ErrorState, TableSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePortfolio, useTrades } from "@/hooks/use-trading";
import { formatMoney, formatPercent, formatPrice, formatShares, formatSignedMoney, signedValueClass } from "@/lib/format";
import { cn } from "@/lib/utils";

import { TradeForm } from "./trade-form";
import { TradeHistoryTable } from "./trade-history-table";

function AccountCard() {
  const { data, error, mutate } = usePortfolio();
  return (
    <Card className="gap-4">
      <CardHeader>
        <CardTitle>模擬帳戶</CardTitle>
        <CardDescription>{data ? `第 ${data.account.cycle} 輪・初始資金 ${formatMoney(data.account.initial_cash)}` : "載入中"}</CardDescription>
      </CardHeader>
      <CardContent>
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : !data ? (
          <TableSkeleton rows={3} />
        ) : (
          <dl className="space-y-2 text-sm" data-testid="account-card">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">現金餘額</dt>
              <dd className="font-semibold tabular" data-testid="account-cash">
                {formatMoney(data.cash_twd)}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">持股市值</dt>
              <dd className="tabular">{formatMoney(data.market_value_twd)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">總資產</dt>
              <dd className="tabular">{formatMoney(data.total_assets_twd)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">投資報酬率</dt>
              <dd className={cn("tabular", signedValueClass(data.roi_pct))}>{formatPercent(data.roi_pct)}</dd>
            </div>
          </dl>
        )}
      </CardContent>
    </Card>
  );
}

function HoldingCard({ symbol }: { symbol: string }) {
  const { data } = usePortfolio();
  if (!data) return null;
  const position = data.positions.find((item) => item.symbol === symbol);
  return (
    <Card className="gap-4">
      <CardHeader>
        <CardTitle>目前持股：{symbol}</CardTitle>
      </CardHeader>
      <CardContent>
        {position ? (
          <dl className="space-y-2 text-sm" data-testid="holding-card">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">持股</dt>
              <dd className="tabular">{formatShares(position.shares)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">平均成本</dt>
              <dd className="tabular">
                {formatPrice(position.avg_cost)} {position.currency}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">未實現損益</dt>
              <dd className={cn("tabular", signedValueClass(position.unrealized_pnl_twd))}>
                {formatSignedMoney(position.unrealized_pnl_twd)}（{formatPercent(position.unrealized_pnl_pct)}）
              </dd>
            </div>
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">尚未持有這檔股票。</p>
        )}
      </CardContent>
    </Card>
  );
}

function RecentTrades() {
  const { data, error, mutate } = useTrades("current", 10);
  return (
    <Card className="mt-6 gap-4">
      <CardHeader>
        <CardTitle>最近交易</CardTitle>
        <CardDescription>本輪最近 10 筆模擬成交</CardDescription>
        <CardAction>
          <Button asChild variant="outline" size="sm">
            <Link href="/portfolio">查看全部</Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : !data ? (
          <TableSkeleton rows={3} />
        ) : data.trades.length ? (
          <TradeHistoryTable trades={data.trades} />
        ) : (
          <EmptyState title="還沒有交易紀錄" description="完成第一筆模擬下單後會顯示在這裡" />
        )}
      </CardContent>
    </Card>
  );
}

export function TradingView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const symbol = searchParams.get("symbol")?.trim().toUpperCase() || null;
  const setSymbol = (value: string | null) =>
    router.replace(value ? `/trading?symbol=${encodeURIComponent(value)}` : "/trading");

  return (
    <>
      <PageHeader title="模擬下單" description="以 NT$1,000,000 虛擬資金練習買賣台股與美股；美股依臺灣銀行 USD/TWD 匯率換算台幣" />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <TradeForm key={symbol ?? "none"} symbol={symbol} onSymbolChange={setSymbol} />
        <aside className="min-w-0 space-y-6">
          <AccountCard />
          {symbol ? <HoldingCard symbol={symbol} /> : null}
        </aside>
      </div>
      <RecentTrades />
    </>
  );
}

export function TradingSkeleton() {
  return <CardSkeleton rows={8} />;
}

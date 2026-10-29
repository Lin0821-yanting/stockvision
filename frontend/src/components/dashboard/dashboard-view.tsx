"use client";

import Link from "next/link";
import { ArrowRight, BellRing, GitCompareArrows } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/states";
import { MarketStatusPills } from "@/components/layout/market-status-pills";
import { AllocationBar } from "@/components/portfolio/allocation-bar";
import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { TradeSideBadge } from "@/components/trading/trade-history-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAlerts } from "@/hooks/use-alerts";
import { usePortfolio, useTrades } from "@/hooks/use-trading";
import { useWatchlist } from "@/hooks/use-watchlist";
import {
  formatDateTime,
  formatMoney,
  formatPercent,
  formatPrice,
  formatShares,
  formatSignedMoney,
  signedValueClass,
  toneOf,
  TONE_ARROW,
  TONE_TEXT_CLASS,
} from "@/lib/format";
import { cn } from "@/lib/utils";

import { ChangeBarChart } from "./change-bar-chart";
import { WatchlistCard } from "./watchlist-table";

function AccountOverview() {
  const { data, error, mutate } = usePortfolio();
  if (error && !data) return <ErrorState error={error} title="無法取得模擬帳戶" onRetry={() => mutate()} />;
  if (!data) return <Skeleton className="h-40 w-full rounded-xl" />;
  const tone = toneOf(data.total_pnl_twd);
  return (
    <div className="grid gap-3 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,2fr)]">
      <Card className="gap-2 py-5" data-testid="hero-total-assets">
        <CardContent className="px-5">
          <p className="text-sm text-muted-foreground">模擬總資產</p>
          <p className="mt-1 text-4xl font-semibold tracking-tight whitespace-nowrap sm:text-5xl">
            {formatMoney(data.total_assets_twd)}
          </p>
          <p className={cn("mt-2 text-sm font-medium", TONE_TEXT_CLASS[tone])}>
            <span aria-hidden>{TONE_ARROW[tone]} </span>
            {formatSignedMoney(data.total_pnl_twd)}（{formatPercent(data.roi_pct)}）
            <span className="ml-1 font-normal text-muted-foreground">相較初始資金 {formatMoney(data.account.initial_cash)}</span>
          </p>
          <p className="mt-3 text-xs text-muted-foreground">模擬成交，不代表真實市場價格或成交・第 {data.account.cycle} 輪</p>
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="現金餘額" value={formatMoney(data.cash_twd)} testId="dash-cash" />
        <StatCard label="持股市值" value={formatMoney(data.market_value_twd)} hint={`${data.positions.length} 檔持股`} />
        <StatCard
          label="未實現損益"
          value={formatSignedMoney(data.unrealized_pnl_twd)}
          valueClassName={signedValueClass(data.unrealized_pnl_twd)}
        />
        <StatCard
          label="已實現損益"
          value={formatSignedMoney(data.realized_pnl_twd)}
          valueClassName={signedValueClass(data.realized_pnl_twd)}
        />
      </div>
    </div>
  );
}

function WatchlistMovers() {
  const { data } = useWatchlist();
  return (
    <Card className="min-w-0 gap-4">
      <CardHeader>
        <CardTitle>自選股今日漲跌幅</CardTitle>
        <CardDescription>右側上漲（紅）、左側下跌（綠）</CardDescription>
      </CardHeader>
      <CardContent>{data ? <ChangeBarChart items={data.items} /> : <Skeleton className="h-40 w-full" />}</CardContent>
    </Card>
  );
}

function RecentTrades() {
  const { data, error, mutate } = useTrades("current", 5);
  return (
    <Card className="min-w-0 gap-4">
      <CardHeader>
        <CardTitle>最近交易</CardTitle>
        <CardAction>
          <Button asChild variant="ghost" size="sm">
            <Link href="/portfolio">
              全部
              <ArrowRight />
            </Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : !data ? (
          <TableSkeleton rows={3} />
        ) : data.trades.length ? (
          <ul className="divide-y" data-testid="recent-trades">
            {data.trades.map((trade) => (
              <li key={trade.id} className="flex items-center gap-3 py-2.5 text-sm">
                <TradeSideBadge side={trade.side} />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">
                    {trade.name} <span className="font-mono text-xs text-muted-foreground">{trade.symbol}</span>
                  </p>
                  <p className="text-xs text-muted-foreground tabular">
                    {formatShares(trade.shares)} × {formatPrice(trade.price)} {trade.currency}・{formatDateTime(trade.created_at)}
                  </p>
                </div>
                <span className="tabular">{formatMoney(trade.amount_twd)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="還沒有交易"
            action={
              <Button asChild size="sm">
                <Link href="/trading">開始模擬下單</Link>
              </Button>
            }
            className="p-6"
          />
        )}
      </CardContent>
    </Card>
  );
}

function ActiveAlerts() {
  const { data, error, mutate } = useAlerts();
  const active = data?.alerts.filter((alert) => alert.is_active) ?? [];
  return (
    <Card className="min-w-0 gap-4">
      <CardHeader>
        <CardTitle>啟用中的價格提醒</CardTitle>
        <CardDescription>
          {data?.monitor.running ? `背景排程運行中（交易時段每 ${data.monitor.interval_seconds} 秒）` : "網站取得行情時同步檢查"}
        </CardDescription>
        <CardAction>
          <Button asChild variant="ghost" size="sm">
            <Link href="/alerts">
              管理
              <ArrowRight />
            </Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : !data ? (
          <TableSkeleton rows={3} />
        ) : active.length ? (
          <ul className="divide-y" data-testid="active-alerts">
            {active.slice(0, 6).map((alert) => (
              <li key={alert.id} className="flex items-center gap-3 py-2.5 text-sm">
                <BellRing className="size-4 shrink-0 text-primary" aria-hidden />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">
                    {alert.name} <span className="font-mono text-xs text-muted-foreground">{alert.symbol}</span>
                  </p>
                  <p className="text-xs text-muted-foreground">{alert.condition_label}</p>
                </div>
                {alert.last_checked_price != null ? (
                  <span className="flex items-center gap-1.5 text-xs tabular">
                    {alert.last_price_kind ? <QuoteKindBadge kind={alert.last_price_kind} className="px-1.5 py-0 text-[10px]" /> : null}
                    {formatPrice(alert.last_checked_price)}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={BellRing}
            title="沒有啟用中的提醒"
            action={
              <Button asChild size="sm" variant="outline">
                <Link href="/alerts">新增提醒</Link>
              </Button>
            }
            className="p-6"
          />
        )}
      </CardContent>
    </Card>
  );
}

function AllocationCard() {
  const { data } = usePortfolio();
  if (!data || !data.positions.length) return null;
  return (
    <Card className="min-w-0 gap-4">
      <CardHeader>
        <CardTitle>持股配置</CardTitle>
        <CardAction>
          <Button asChild variant="ghost" size="sm">
            <Link href="/portfolio">
              投資組合
              <ArrowRight />
            </Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <AllocationBar portfolio={data} />
      </CardContent>
    </Card>
  );
}

function CompareShortcut() {
  const shortcuts = [
    { label: "台積電 vs 鴻海", href: "/compare?symbols=2330,2317&period=3M" },
    { label: "台積電 vs NVIDIA", href: "/compare?symbols=2330,NVDA&period=6M" },
    { label: "Apple vs Microsoft", href: "/compare?symbols=AAPL,MSFT&period=1Y" },
  ];
  return (
    <Card className="min-w-0 gap-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitCompareArrows className="size-4 text-primary" aria-hidden />
          股票比較捷徑
        </CardTitle>
        <CardDescription>標準化走勢由 Python Pandas 計算，也可以在自選股表格勾選股票比較</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {shortcuts.map((item) => (
          <Button key={item.href} asChild variant="outline" size="sm">
            <Link href={item.href}>{item.label}</Link>
          </Button>
        ))}
        <Badge variant="secondary" className="self-center">
          支援台股、美股混合比較
        </Badge>
      </CardContent>
    </Card>
  );
}

export function DashboardView() {
  return (
    <>
      <PageHeader title="投資總覽" description="自選股行情、模擬投資組合與價格提醒" actions={<MarketStatusPills />} />
      <div className="space-y-6">
        <AccountOverview />
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
          <WatchlistCard />
          <WatchlistMovers />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <RecentTrades />
          <ActiveAlerts />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <AllocationCard />
          <CompareShortcut />
        </div>
      </div>
    </>
  );
}

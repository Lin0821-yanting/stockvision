"use client";

import { useState } from "react";
import Link from "next/link";
import { Wallet } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { CardSkeleton, EmptyState, ErrorState, TableSkeleton } from "@/components/common/states";
import { TradeHistoryTable } from "@/components/trading/trade-history-table";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePortfolio, useTrades } from "@/hooks/use-trading";
import { formatDateTime } from "@/lib/format";

import { AllocationBar } from "./allocation-bar";
import { PortfolioSummary } from "./portfolio-summary";
import { PositionsTable } from "./positions-table";
import { ResetAccountDialog } from "./reset-account-dialog";

function TradeHistoryCard() {
  const [scope, setScope] = useState<"current" | "all">("current");
  const { data, error, mutate } = useTrades(scope, 500);
  return (
    <Card className="gap-4">
      <CardHeader>
        <CardTitle>交易紀錄</CardTitle>
        <CardDescription>所有模擬成交都保存在 SQLite；重置帳戶後舊紀錄仍保留</CardDescription>
        <CardAction>
          <Tabs value={scope} onValueChange={(value) => setScope(value as "current" | "all")}>
            <TabsList aria-label="交易紀錄範圍">
              <TabsTrigger value="current">本輪</TabsTrigger>
              <TabsTrigger value="all">全部</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardAction>
      </CardHeader>
      <CardContent>
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : !data ? (
          <TableSkeleton rows={4} />
        ) : data.trades.length ? (
          <TradeHistoryTable trades={data.trades} showCycle={scope === "all"} />
        ) : (
          <EmptyState title="這個範圍沒有交易紀錄" description="到模擬下單頁面完成第一筆交易" />
        )}
      </CardContent>
    </Card>
  );
}

export function PortfolioView() {
  const { data, error, mutate } = usePortfolio();

  return (
    <>
      <PageHeader
        title="投資組合"
        description={
          data
            ? `估值時間 ${formatDateTime(data.as_of)}・${data.disclaimer}`
            : "持股、損益、總資產與完整交易紀錄"
        }
        actions={<ResetAccountDialog />}
      />
      <div className="space-y-6">
        {error && !data ? (
          <ErrorState error={error} onRetry={() => mutate()} />
        ) : !data ? (
          <CardSkeleton rows={4} />
        ) : (
          <>
            <PortfolioSummary portfolio={data} />
            <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_380px]">
              <Card className="min-w-0 gap-4">
                <CardHeader>
                  <CardTitle>持股明細</CardTitle>
                  <CardDescription>
                    市值以最新可取得價格計算
                    {data.fx ? `；美股以 USD/TWD ${data.fx.rate.toFixed(4)}（${data.fx.rate_date}）換算` : ""}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {data.positions.length ? (
                    <PositionsTable positions={data.positions} />
                  ) : (
                    <EmptyState
                      icon={Wallet}
                      title="目前沒有持股"
                      description="用虛擬資金買進第一檔股票吧"
                      action={
                        <Button asChild size="sm">
                          <Link href="/trading">前往模擬下單</Link>
                        </Button>
                      }
                    />
                  )}
                </CardContent>
              </Card>
              <Card className="min-w-0 gap-4">
                <CardHeader>
                  <CardTitle>持股配置</CardTitle>
                  <CardDescription>各持股占股票總市值的比例</CardDescription>
                </CardHeader>
                <CardContent>
                  <AllocationBar portfolio={data} />
                </CardContent>
              </Card>
            </div>
          </>
        )}
        <TradeHistoryCard />
      </div>
    </>
  );
}

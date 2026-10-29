"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BellRing, Info, LoaderCircle, Plus, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/page-header";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAlertEvents, useAlerts, useRefreshAlerts } from "@/hooks/use-alerts";
import { formatDateTime } from "@/lib/format";
import { errorMessage } from "@/services/api-client";
import { alertsApi } from "@/services/alerts";
import type { MonitorStatus, PriceAlert } from "@/types/api";

import { AlertEventsTable } from "./alert-events-table";
import { AlertFormDialog } from "./alert-form-dialog";
import { AlertsTable } from "./alerts-table";

function MonitorCard({ monitor }: { monitor?: MonitorStatus }) {
  return (
    <Card className="gap-3 border-primary/30 bg-primary/5" data-testid="monitor-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Info className="size-4 text-primary" aria-hidden />
          提醒的執行條件
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p>
          {monitor?.explanation ??
            "提醒由 Python 後端判斷：前端取得新行情時會同步檢查；後端運行期間，背景排程也會在交易時段定期檢查。若網站與後端服務都已關閉，系統無法監控價格。"}
        </p>
        {monitor ? (
          <ul className="grid gap-1 text-xs text-muted-foreground sm:grid-cols-2">
            <li>
              背景排程：
              {monitor.running ? `運行中，交易時段每 ${monitor.interval_seconds} 秒檢查一次` : "未啟用"}
            </li>
            <li>目前開盤市場：{monitor.markets_open.length ? monitor.markets_open.map((m) => (m === "TW" ? "台股" : "美股")).join("、") : "無"}</li>
            <li>上次執行：{monitor.last_run_at ? formatDateTime(monitor.last_run_at) : "尚未執行"}</li>
            <li>結果：{monitor.last_result}</li>
          </ul>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function AlertsView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const presetSymbol = searchParams.get("symbol")?.trim().toUpperCase() || null;
  const alerts = useAlerts();
  const events = useAlertEvents();
  const refresh = useRefreshAlerts();
  const [dialog, setDialog] = useState<{ open: boolean; alert: PriceAlert | null; symbol: string | null }>({
    open: Boolean(presetSymbol),
    alert: null,
    symbol: presetSymbol,
  });
  const [checking, setChecking] = useState(false);

  function closeDialog(open: boolean) {
    setDialog((current) => ({ ...current, open }));
    if (!open && presetSymbol) router.replace("/alerts");
  }

  async function checkNow() {
    setChecking(true);
    try {
      const result = await alertsApi.check();
      toast.success(
        result.triggered.length
          ? `已檢查 ${result.checked_alerts} 個提醒，${result.triggered.length} 個條件成立並已發出通知`
          : `已檢查 ${result.checked_alerts} 個提醒，條件都尚未成立`,
      );
      if (result.errors.length) toast.error(`部分股票取價失敗：${result.errors.join("；")}`);
      await refresh();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setChecking(false);
    }
  }

  const list = alerts.data?.alerts ?? [];

  return (
    <>
      <PageHeader
        title="價格提醒"
        description="設定低價、高價與 20 日新低提醒；觸發時顯示站內通知"
        actions={
          <>
            <Button variant="outline" onClick={checkNow} disabled={checking || !list.length} data-testid="check-alerts">
              {checking ? <LoaderCircle className="animate-spin" /> : <RefreshCw />}
              立即檢查
            </Button>
            <Button onClick={() => setDialog({ open: true, alert: null, symbol: null })} data-testid="new-alert">
              <Plus />
              新增提醒
            </Button>
          </>
        }
      />
      <div className="space-y-6">
        <MonitorCard monitor={alerts.data?.monitor} />

        <Card className="gap-4">
          <CardHeader>
            <CardTitle>我的提醒</CardTitle>
            <CardDescription>開關可停用或重新啟用；重新啟用或修改條件後會立即重新檢查</CardDescription>
          </CardHeader>
          <CardContent>
            {alerts.error && !alerts.data ? (
              <ErrorState error={alerts.error} onRetry={() => alerts.mutate()} />
            ) : !alerts.data ? (
              <TableSkeleton rows={3} />
            ) : list.length ? (
              <AlertsTable alerts={list} onEdit={(alert) => setDialog({ open: true, alert, symbol: alert.symbol })} />
            ) : (
              <EmptyState
                icon={BellRing}
                title="還沒有價格提醒"
                description="例如：台積電 2330 價格 ≤ 900 元時通知我"
                action={
                  <Button size="sm" onClick={() => setDialog({ open: true, alert: null, symbol: "2330" })}>
                    <Plus />
                    建立第一個提醒
                  </Button>
                }
              />
            )}
          </CardContent>
        </Card>

        <Card className="gap-4">
          <CardHeader>
            <CardTitle>歷史觸發紀錄</CardTitle>
            <CardDescription>每次觸發的價格、來源與時間；刪除提醒後紀錄仍保留</CardDescription>
          </CardHeader>
          <CardContent>
            {events.error && !events.data ? (
              <ErrorState error={events.error} onRetry={() => events.mutate()} />
            ) : !events.data ? (
              <TableSkeleton rows={3} />
            ) : events.data.length ? (
              <AlertEventsTable events={events.data} />
            ) : (
              <EmptyState title="尚未有提醒被觸發" />
            )}
          </CardContent>
        </Card>
      </div>

      {dialog.open ? (
        <AlertFormDialog
          key={dialog.alert?.id ?? dialog.symbol ?? "new"}
          open={dialog.open}
          onOpenChange={closeDialog}
          alert={dialog.alert}
          initialSymbol={dialog.symbol}
        />
      ) : null}
    </>
  );
}

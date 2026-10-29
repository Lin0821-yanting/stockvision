"use client";

import { useState } from "react";
import { Pencil, Trash } from "lucide-react";
import { toast } from "sonner";

import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useRefreshAlerts } from "@/hooks/use-alerts";
import { formatDateTime, formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";
import { errorMessage } from "@/services/api-client";
import { alertsApi } from "@/services/alerts";
import type { PriceAlert } from "@/types/api";

const STATUS_CLASS: Record<PriceAlert["status"], string> = {
  monitoring: "border-primary/40 bg-primary/15 text-primary",
  triggered: "border-amber-500/40 bg-amber-500/15 text-amber-300",
  disabled: "text-muted-foreground",
};

export function AlertsTable({ alerts, onEdit }: { alerts: PriceAlert[]; onEdit: (alert: PriceAlert) => void }) {
  const refresh = useRefreshAlerts();
  const [deleting, setDeleting] = useState<PriceAlert | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function toggle(alert: PriceAlert, active: boolean) {
    setBusyId(alert.id);
    try {
      const result = await alertsApi.update(alert.id, { is_active: active });
      const suffix = result.triggered.length ? "（條件已成立，已發出通知）" : "";
      toast.success(`${active ? "已啟用" : "已停用"} ${alert.name} 的提醒${suffix}`);
      await refresh();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setBusyId(null);
    }
  }

  async function remove(alert: PriceAlert) {
    try {
      await alertsApi.remove(alert.id);
      toast.success(`已刪除 ${alert.name} 的提醒（觸發紀錄會保留）`);
      await refresh();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setDeleting(null);
    }
  }

  return (
    <>
      <Table data-testid="alerts-table">
        <TableHeader>
          <TableRow>
            <TableHead>股票</TableHead>
            <TableHead>條件</TableHead>
            <TableHead>觸發方式</TableHead>
            <TableHead>狀態</TableHead>
            <TableHead className="text-right">最近檢查</TableHead>
            <TableHead className="text-right">觸發次數</TableHead>
            <TableHead>啟用</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody className="tabular">
          {alerts.map((alert) => (
            <TableRow key={alert.id} data-testid={`alert-row-${alert.id}`}>
              <TableCell>
                <p className="font-medium">{alert.name}</p>
                <p className="font-mono text-xs text-muted-foreground">{alert.symbol}</p>
              </TableCell>
              <TableCell>
                <p>{alert.condition_label}</p>
                {alert.note ? <p className="text-xs text-muted-foreground">{alert.note}</p> : null}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {alert.trigger_mode === "ONCE" ? "一次" : "每次跨越"}
              </TableCell>
              <TableCell>
                <Badge variant="outline" className={cn(STATUS_CLASS[alert.status])}>
                  {alert.status_label}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                {alert.last_checked_at ? (
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="flex items-center gap-1.5">
                      {alert.last_price_kind ? <QuoteKindBadge kind={alert.last_price_kind} className="px-1.5 py-0 text-[10px]" /> : null}
                      {formatPrice(alert.last_checked_price)}
                    </span>
                    <span className="text-xs text-muted-foreground">{formatDateTime(alert.last_checked_at)}</span>
                  </div>
                ) : (
                  <span className="text-xs text-muted-foreground">尚未檢查</span>
                )}
              </TableCell>
              <TableCell className="text-right">{alert.trigger_count}</TableCell>
              <TableCell>
                <Switch
                  checked={alert.is_active}
                  disabled={busyId === alert.id}
                  onCheckedChange={(checked) => toggle(alert, checked)}
                  aria-label={`${alert.is_active ? "停用" : "啟用"} ${alert.name} 的提醒`}
                />
              </TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  <Button variant="ghost" size="icon-sm" onClick={() => onEdit(alert)} aria-label={`編輯 ${alert.name} 的提醒`}>
                    <Pencil />
                  </Button>
                  <Button variant="ghost" size="icon-sm" onClick={() => setDeleting(alert)} aria-label={`刪除 ${alert.name} 的提醒`}>
                    <Trash />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <AlertDialog open={Boolean(deleting)} onOpenChange={(open) => !open && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>刪除這個提醒？</AlertDialogTitle>
            <AlertDialogDescription>
              {deleting ? `${deleting.name}（${deleting.symbol}）${deleting.condition_label}。` : ""}
              刪除後不再監控，但歷史觸發紀錄會保留。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction className={buttonVariants({ variant: "destructive" })} onClick={() => deleting && remove(deleting)}>
              刪除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

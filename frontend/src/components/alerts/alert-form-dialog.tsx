"use client";

import { useState } from "react";
import { LoaderCircle } from "lucide-react";
import { toast } from "sonner";

import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { StockSearch } from "@/components/stock/stock-search";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRefreshAlerts } from "@/hooks/use-alerts";
import { useStockDetail } from "@/hooks/use-market";
import { formatPrice } from "@/lib/format";
import { errorMessage } from "@/services/api-client";
import { alertsApi } from "@/services/alerts";
import type { AlertCondition, AlertMutation, PriceAlert, TriggerMode } from "@/types/api";

const CONDITIONS: { value: AlertCondition; label: string }[] = [
  { value: "PRICE_LTE", label: "價格低於或等於（≤）目標價" },
  { value: "PRICE_GTE", label: "價格高於或等於（≥）目標價" },
  { value: "NEW_20D_LOW", label: "創 20 日新低（加分條件）" },
];

const MODES: { value: TriggerMode; label: string }[] = [
  { value: "ONCE", label: "觸發一次後自動停用" },
  { value: "EVERY_CROSS", label: "每次條件由不成立變成立都通知" },
];

function CurrentPrice({ symbol }: { symbol: string }) {
  const { data } = useStockDetail(symbol);
  if (!data) return <p className="text-xs text-muted-foreground">讀取目前價格中…</p>;
  return (
    <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
      目前價格 <span className="font-medium text-foreground tabular">{formatPrice(data.quote.price)} {data.stock.currency}</span>
      <QuoteKindBadge kind={data.quote.kind} />
      {data.low_20d != null ? <span>・前 20 日最低收盤 {formatPrice(data.low_20d)}</span> : null}
    </p>
  );
}

export function AlertFormDialog({
  open,
  onOpenChange,
  alert,
  initialSymbol,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  alert?: PriceAlert | null;
  initialSymbol?: string | null;
}) {
  const editing = Boolean(alert);
  const [symbol, setSymbol] = useState<string | null>(alert?.symbol ?? initialSymbol ?? null);
  const [condition, setCondition] = useState<AlertCondition>(alert?.condition ?? "PRICE_LTE");
  const [target, setTarget] = useState(alert?.target_price != null ? String(alert.target_price) : "");
  const [mode, setMode] = useState<TriggerMode>(alert?.trigger_mode ?? "ONCE");
  const [note, setNote] = useState(alert?.note ?? "");
  const [submitting, setSubmitting] = useState(false);
  const refresh = useRefreshAlerts();

  const needsTarget = condition !== "NEW_20D_LOW";
  const targetValue = Number(target);
  const targetValid = !needsTarget || (target.trim() !== "" && Number.isFinite(targetValue) && targetValue > 0);

  // 觸發細節由通知鈴鐺統一跳出，這裡只回報建立結果，避免同一件事出現兩個 toast
  function report(result: AlertMutation, verb: string) {
    const suffix = result.triggered.length ? "（條件已成立，已發出通知）" : "";
    toast.success(`${verb}提醒：${result.alert.name} ${result.alert.condition_label}${suffix}`);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!symbol || !targetValid) return;
    setSubmitting(true);
    const payload = {
      condition,
      target_price: needsTarget ? targetValue : null,
      trigger_mode: mode,
      note: note.trim() || null,
    };
    try {
      const result = alert ? await alertsApi.update(alert.id, payload) : await alertsApi.create({ symbol, ...payload });
      report(result, editing ? "已更新" : "已建立");
      await refresh();
      onOpenChange(false);
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4" data-testid="alert-form">
          <DialogHeader>
            <DialogTitle>{editing ? "編輯價格提醒" : "新增價格提醒"}</DialogTitle>
            <DialogDescription>由 Python 後端判斷條件；建立後會立刻用最新價格檢查一次。</DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            <Label>股票</Label>
            {symbol ? (
              <div className="flex items-center justify-between gap-2 rounded-md border px-3 py-2">
                <span className="font-medium">
                  {alert?.name ?? ""} <span className="font-mono">{symbol}</span>
                </span>
                {!editing ? (
                  <Button type="button" variant="ghost" size="sm" onClick={() => setSymbol(null)}>
                    更換
                  </Button>
                ) : null}
              </div>
            ) : (
              <StockSearch onSelect={(stock) => setSymbol(stock.symbol)} />
            )}
            {symbol ? <CurrentPrice symbol={symbol} /> : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="alert-condition">提醒條件</Label>
            <Select value={condition} onValueChange={(value) => setCondition(value as AlertCondition)}>
              <SelectTrigger id="alert-condition" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CONDITIONS.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {needsTarget ? (
            <div className="space-y-2">
              <Label htmlFor="alert-target">目標價格</Label>
              <Input
                id="alert-target"
                inputMode="decimal"
                value={target}
                onChange={(event) => setTarget(event.target.value.replace(/[^\d.]/g, ""))}
                placeholder="例如 900"
                aria-invalid={!targetValid}
                className="tabular"
              />
              {!targetValid ? <p className="text-xs text-destructive">請輸入大於 0 的價格</p> : null}
            </div>
          ) : (
            <p className="rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
              當最新價格低於前 20 個交易日（不含當日）的最低收盤價時觸發，由 Pandas 計算。
            </p>
          )}

          <div className="space-y-2">
            <Label htmlFor="alert-mode">觸發方式</Label>
            <Select value={mode} onValueChange={(value) => setMode(value as TriggerMode)}>
              <SelectTrigger id="alert-mode" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODES.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="alert-note">備註（選填）</Label>
            <Input id="alert-note" value={note} maxLength={200} onChange={(event) => setNote(event.target.value)} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button type="submit" disabled={!symbol || !targetValid || submitting} data-testid="save-alert">
              {submitting ? <LoaderCircle className="animate-spin" /> : null}
              {editing ? "儲存變更" : "建立提醒"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

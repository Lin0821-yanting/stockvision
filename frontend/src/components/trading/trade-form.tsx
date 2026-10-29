"use client";

import { useState } from "react";
import { LoaderCircle, TriangleAlert } from "lucide-react";
import useSWR from "swr";
import { toast } from "sonner";

import { ErrorState } from "@/components/common/states";
import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { PriceChange } from "@/components/stock/price-change";
import { StockSearch } from "@/components/stock/stock-search";
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
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebounce } from "@/hooks/use-debounce";
import { useStockDetail } from "@/hooks/use-market";
import { usePortfolio, useRefreshAccountData } from "@/hooks/use-trading";
import { formatDate, formatDateTime, formatMoney, formatPrice, formatShares, formatSignedMoney, signedValueClass } from "@/lib/format";
import { MARKET_LABEL, MARKET_TIMEZONE, marketOf } from "@/lib/market";
import { cn } from "@/lib/utils";
import { errorMessage } from "@/services/api-client";
import { tradingApi } from "@/services/trading";
import type { TradePreview, TradeSide } from "@/types/api";

const MAX_SHARES = 10_000_000;
const QUICK_SHARES = {
  TW: [
    { label: "1 股", value: 1 },
    { label: "100 股", value: 100 },
    { label: "1 張", value: 1000 },
    { label: "5 張", value: 5000 },
  ],
  US: [
    { label: "1 股", value: 1 },
    { label: "5 股", value: 5 },
    { label: "10 股", value: 10 },
    { label: "50 股", value: 50 },
  ],
} as const;

function SelectedStock({ symbol, onChange }: { symbol: string; onChange: () => void }) {
  const detail = useStockDetail(symbol);
  if (detail.error && !detail.data) {
    return (
      <div className="space-y-2">
        <ErrorState error={detail.error} title={`無法取得 ${symbol} 的報價`} onRetry={() => detail.mutate()} />
        <Button variant="outline" size="sm" onClick={onChange}>
          更換股票
        </Button>
      </div>
    );
  }
  if (!detail.data) return <Skeleton className="h-16 w-full" />;
  const { stock, quote } = detail.data;
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-muted/30 p-3" data-testid="selected-stock">
      <div className="min-w-0 flex-1">
        <p className="font-medium">
          {stock.name} <span className="font-mono text-muted-foreground">{stock.symbol}</span>
          <span className="ml-2 text-xs text-muted-foreground">{MARKET_LABEL[stock.market]}</span>
        </p>
        <div className="mt-0.5 flex flex-wrap items-center gap-2 text-sm">
          <span className="font-semibold tabular">
            {formatPrice(quote.price)} {stock.currency}
          </span>
          <PriceChange change={quote.change} changePct={quote.change_pct} />
          <QuoteKindBadge kind={quote.kind} />
        </div>
      </div>
      <Button variant="ghost" size="sm" onClick={onChange}>
        更換股票
      </Button>
    </div>
  );
}

function PreviewRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right tabular">{children}</dd>
    </div>
  );
}

function PreviewPanel({ preview, loading, error }: { preview?: TradePreview; loading: boolean; error: unknown }) {
  if (error && !preview) return <ErrorState error={error} title="試算失敗" />;
  if (!preview) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
        {loading ? <LoaderCircle className="size-4 animate-spin" aria-hidden /> : null}
        {loading ? "Python 後端試算中…" : "選擇股票並輸入股數後，會由 Python 後端計算成交金額"}
      </div>
    );
  }
  const timeZone = MARKET_TIMEZONE[preview.market];
  return (
    <div className={cn("rounded-lg border p-4 text-sm", loading && "opacity-60")} data-testid="trade-preview">
      <dl className="divide-y divide-border">
        <PreviewRow label="參考成交價">
          <span className="flex items-center justify-end gap-1.5 font-medium">
            <QuoteKindBadge kind={preview.price_kind} />
            {formatPrice(preview.price)} {preview.currency}
          </span>
          <span className="block text-xs text-muted-foreground">
            {preview.price_source}・{formatDateTime(preview.price_as_of, timeZone)}
          </span>
        </PreviewRow>
        {preview.currency !== "TWD" ? (
          <PreviewRow label="USD/TWD 匯率">
            {preview.fx_rate.toFixed(4)}
            <span className="block text-xs text-muted-foreground">臺灣銀行即期中價 {formatDate(preview.fx_date)}</span>
          </PreviewRow>
        ) : null}
        <PreviewRow label="成交金額">
          {preview.currency !== "TWD" ? (
            <span className="block text-xs text-muted-foreground">{formatMoney(preview.gross_amount, preview.currency)}</span>
          ) : null}
          <span className="font-semibold">{formatMoney(preview.amount_twd)}</span>
        </PreviewRow>
        <PreviewRow label="手續費／證交稅">{formatMoney(preview.fee_twd + preview.tax_twd)}（第一版不計）</PreviewRow>
        <PreviewRow label="交易後現金">
          {formatMoney(preview.cash_before)} → {preview.cash_after != null ? formatMoney(preview.cash_after) : "—"}
        </PreviewRow>
        <PreviewRow label="交易後持股">
          {formatShares(preview.shares_held)} → {preview.shares_after != null ? formatShares(preview.shares_after) : "—"}
        </PreviewRow>
        {preview.side === "SELL" && preview.estimated_realized_pnl_twd != null ? (
          <PreviewRow label="預估已實現損益">
            <span className={signedValueClass(preview.estimated_realized_pnl_twd)}>
              {formatSignedMoney(preview.estimated_realized_pnl_twd)}
            </span>
          </PreviewRow>
        ) : null}
      </dl>
      {!preview.can_execute ? (
        <p role="alert" className="mt-3 flex items-start gap-2 rounded-md bg-destructive/10 p-2.5 text-destructive" data-testid="preview-reason">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          {preview.reason}
        </p>
      ) : null}
    </div>
  );
}

export function TradeForm({ symbol, onSymbolChange }: { symbol: string | null; onSymbolChange: (symbol: string | null) => void }) {
  const [side, setSide] = useState<TradeSide>("BUY");
  const [sharesText, setSharesText] = useState("1000");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const shares = Number(sharesText);
  const validShares = /^\d+$/.test(sharesText) && shares > 0 && shares <= MAX_SHARES;
  const debouncedShares = useDebounce(validShares ? shares : null, 300);
  const market = symbol ? marketOf(symbol) : "TW";

  const detail = useStockDetail(symbol);
  const { data: portfolio } = usePortfolio();
  const holding = symbol ? portfolio?.positions.find((position) => position.symbol === symbol) : undefined;
  const refresh = useRefreshAccountData();

  // 報價更新時（盤中每 10 秒）一併重新試算
  const previewKey =
    symbol && debouncedShares ? ["trade-preview", symbol, side, debouncedShares, detail.data?.quote.price ?? null] : null;
  const preview = useSWR(
    previewKey,
    () => tradingApi.preview({ symbol: symbol!, side, shares: debouncedShares! }),
    { revalidateOnFocus: false, keepPreviousData: true },
  );
  const previewData = previewKey ? preview.data : undefined;
  const previewMatches =
    previewData?.symbol === symbol && previewData?.side === side && previewData?.shares === debouncedShares;

  async function submit() {
    if (!symbol || !validShares) return;
    setSubmitting(true);
    try {
      const result = await tradingApi.execute({ symbol, side, shares });
      toast.success(result.message, { description: result.disclaimer });
      setConfirmOpen(false);
      await refresh();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  const actionLabel = side === "BUY" ? "買進" : "賣出";

  return (
    <Card data-testid="trade-form">
      <CardHeader>
        <CardTitle>模擬下單</CardTitle>
        <CardDescription>成交價由 Python 後端取得：盤中使用即時報價，收盤後使用最近交易日收盤價。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <section className="space-y-2">
          <Label>股票</Label>
          {symbol ? (
            <SelectedStock symbol={symbol} onChange={() => onSymbolChange(null)} />
          ) : (
            <StockSearch onSelect={(stock) => onSymbolChange(stock.symbol)} autoFocus />
          )}
        </section>

        <section className="space-y-2">
          <Label id="side-label">買賣方向</Label>
          <div role="radiogroup" aria-labelledby="side-label" className="grid grid-cols-2 gap-2">
            {(["BUY", "SELL"] as const).map((value) => (
              <Button
                key={value}
                type="button"
                role="radio"
                aria-checked={side === value}
                variant="outline"
                onClick={() => setSide(value)}
                className={cn(
                  side === value && value === "BUY" && "border-up bg-up/15 text-up hover:bg-up/20 hover:text-up",
                  side === value && value === "SELL" && "border-down bg-down/15 text-down hover:bg-down/20 hover:text-down",
                )}
              >
                {value === "BUY" ? "買進" : "賣出"}
              </Button>
            ))}
          </div>
        </section>

        <section className="space-y-2">
          <Label htmlFor="trade-shares">股數</Label>
          <Input
            id="trade-shares"
            inputMode="numeric"
            value={sharesText}
            onChange={(event) => setSharesText(event.target.value.replace(/[^\d]/g, ""))}
            aria-invalid={!validShares}
            aria-describedby="trade-shares-help"
            className="tabular"
          />
          <div className="flex flex-wrap gap-2">
            {QUICK_SHARES[market].map((item) => (
              <Button key={item.label} type="button" variant="secondary" size="sm" onClick={() => setSharesText(String(item.value))}>
                {item.label}
              </Button>
            ))}
            {side === "SELL" && holding ? (
              <Button type="button" variant="secondary" size="sm" onClick={() => setSharesText(String(holding.shares))}>
                全部 {holding.shares.toLocaleString("zh-TW")} 股
              </Button>
            ) : null}
          </div>
          <p id="trade-shares-help" className={cn("text-xs", validShares ? "text-muted-foreground" : "text-destructive")}>
            {validShares
              ? market === "TW"
                ? "台股 1 張 = 1,000 股，也可以輸入零股（1–999 股）"
                : "美股以 1 股為單位（不支援碎股）"
              : `請輸入 1 到 ${MAX_SHARES.toLocaleString("zh-TW")} 之間的整數股數`}
          </p>
        </section>

        <PreviewPanel
          preview={previewData}
          loading={Boolean(previewKey) && (preview.isValidating || !previewMatches)}
          error={preview.error}
        />

        <Button
          size="lg"
          className="w-full"
          disabled={!symbol || !validShares || !previewMatches || !previewData?.can_execute || submitting}
          onClick={() => setConfirmOpen(true)}
          data-testid="submit-trade"
        >
          {submitting ? <LoaderCircle className="animate-spin" /> : null}
          確認{actionLabel}
        </Button>
        <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
          <TriangleAlert className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          模擬成交，不代表真實市場價格或成交。第一版不計手續費與證交稅。
        </p>
      </CardContent>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              確認模擬{actionLabel} {previewData?.name} {previewData?.symbol}？
            </AlertDialogTitle>
            <AlertDialogDescription>
              {formatShares(shares)}，參考價 {formatPrice(previewData?.price)} {previewData?.currency}，預估金額{" "}
              {formatMoney(previewData?.amount_twd)}。實際成交價以送出當下後端取得的最新價格為準。模擬成交，不代表真實市場價格或成交。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={submitting}>取消</AlertDialogCancel>
            <AlertDialogAction
              disabled={submitting}
              onClick={(event) => {
                event.preventDefault();
                void submit();
              }}
              data-testid="confirm-trade"
            >
              {submitting ? <LoaderCircle className="animate-spin" /> : null}
              確認送出
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}

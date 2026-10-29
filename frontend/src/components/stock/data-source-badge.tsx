import { Badge } from "@/components/ui/badge";
import { formatDate, formatDateTime, formatTime } from "@/lib/format";
import { MARKET_TIMEZONE, MARKET_TZ_LABEL } from "@/lib/market";
import { cn } from "@/lib/utils";
import type { Quote } from "@/types/api";

export function QuoteKindBadge({ kind, className }: { kind: Quote["kind"]; className?: string }) {
  if (kind === "realtime") {
    return (
      <Badge className={cn("border-primary/40 bg-primary/15 text-primary", className)} title="交易時段的盤中報價">
        <span className="size-1.5 animate-pulse rounded-full bg-primary" aria-hidden />
        盤中
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className={cn("text-muted-foreground", className)} title="收盤或最近交易日資料，非即時報價">
      收盤
    </Badge>
  );
}

/** 每個價格都標示：盤中或收盤、資料來源、報價時間、資料日期與後端取得時間 */
export function DataSourceBadge({ quote, className }: { quote: Quote; className?: string }) {
  const timeZone = MARKET_TIMEZONE[quote.market];
  return (
    <div className={cn("space-y-1 text-xs text-muted-foreground", className)} data-testid="data-source">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <QuoteKindBadge kind={quote.kind} />
        <span>來源：{quote.source}</span>
        <span aria-hidden>·</span>
        <span>
          報價時間 {formatDateTime(quote.as_of, timeZone)}（{MARKET_TZ_LABEL[quote.market]}）
        </span>
        <span aria-hidden>·</span>
        <span>資料日期 {formatDate(quote.trade_date)}</span>
        <span aria-hidden>·</span>
        <span>更新於 {formatTime(quote.fetched_at)}</span>
      </div>
      {quote.note ? <p>{quote.note}</p> : null}
    </div>
  );
}

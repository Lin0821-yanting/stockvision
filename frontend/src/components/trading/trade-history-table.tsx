import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDateTime, formatMoney, formatPrice, formatShares, formatSignedMoney, signedValueClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Trade } from "@/types/api";

export function TradeSideBadge({ side }: { side: Trade["side"] }) {
  // 台股慣例：買進紅、賣出綠；同時標示文字
  return (
    <Badge variant="outline" className={side === "BUY" ? "border-up/40 text-up" : "border-down/40 text-down"}>
      {side === "BUY" ? "買進" : "賣出"}
    </Badge>
  );
}

export function TradeHistoryTable({ trades, showCycle = false }: { trades: Trade[]; showCycle?: boolean }) {
  return (
    <Table data-testid="trade-history">
      <TableHeader>
        <TableRow>
          <TableHead>時間</TableHead>
          {showCycle ? <TableHead>回合</TableHead> : null}
          <TableHead>股票</TableHead>
          <TableHead>方向</TableHead>
          <TableHead className="text-right">股數</TableHead>
          <TableHead className="text-right">成交價</TableHead>
          <TableHead className="text-right">金額（NT$）</TableHead>
          <TableHead className="text-right">已實現損益</TableHead>
          <TableHead>價格來源</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="tabular">
        {trades.map((trade) => (
          <TableRow key={trade.id}>
            <TableCell className="text-muted-foreground">{formatDateTime(trade.created_at)}</TableCell>
            {showCycle ? <TableCell>第 {trade.cycle} 輪</TableCell> : null}
            <TableCell>
              <span className="font-medium">{trade.name}</span>
              <span className="ml-1.5 font-mono text-xs text-muted-foreground">{trade.symbol}</span>
            </TableCell>
            <TableCell>
              <TradeSideBadge side={trade.side} />
            </TableCell>
            <TableCell className="text-right">{formatShares(trade.shares)}</TableCell>
            <TableCell className="text-right">
              {formatPrice(trade.price)}
              <span className="ml-1 text-xs text-muted-foreground">{trade.currency}</span>
              {trade.currency !== "TWD" ? (
                <p className="text-xs text-muted-foreground">匯率 {trade.fx_rate.toFixed(4)}</p>
              ) : null}
            </TableCell>
            <TableCell className="text-right">{formatMoney(trade.amount_twd)}</TableCell>
            <TableCell className={cn("text-right", signedValueClass(trade.realized_pnl_twd))}>
              {trade.realized_pnl_twd != null ? formatSignedMoney(trade.realized_pnl_twd) : "—"}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <QuoteKindBadge kind={trade.price_kind} />
                {trade.price_source}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

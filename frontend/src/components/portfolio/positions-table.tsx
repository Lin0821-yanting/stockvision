import Link from "next/link";

import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { PriceChange } from "@/components/stock/price-change";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatMoney, formatPercent, formatPrice, formatShares, formatSignedMoney, signedValueClass } from "@/lib/format";
import { MARKET_LABEL } from "@/lib/market";
import { cn } from "@/lib/utils";
import type { Position } from "@/types/api";

export function PositionsTable({ positions }: { positions: Position[] }) {
  return (
    <Table data-testid="positions-table">
      <TableHeader>
        <TableRow>
          <TableHead>股票</TableHead>
          <TableHead className="text-right">持股</TableHead>
          <TableHead className="text-right">平均成本</TableHead>
          <TableHead className="text-right">現價</TableHead>
          <TableHead className="text-right">今日漲跌</TableHead>
          <TableHead className="text-right">市值（NT$）</TableHead>
          <TableHead className="text-right">未實現損益</TableHead>
          <TableHead className="text-right">已實現（本輪）</TableHead>
          <TableHead className="text-right">占比</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody className="tabular">
        {positions.map((position) => (
          <TableRow key={`${position.market}-${position.symbol}`}>
            <TableCell>
              <div className="flex items-center gap-2">
                <div>
                  <p className="font-medium">{position.name}</p>
                  <p className="font-mono text-xs text-muted-foreground">{position.symbol}</p>
                </div>
                <Badge variant="secondary">{MARKET_LABEL[position.market]}</Badge>
              </div>
            </TableCell>
            <TableCell className="text-right">{formatShares(position.shares)}</TableCell>
            <TableCell className="text-right">
              {formatPrice(position.avg_cost)}
              <span className="ml-1 text-xs text-muted-foreground">{position.currency}</span>
            </TableCell>
            <TableCell className="text-right">
              {position.current_price != null ? (
                <div className="flex flex-col items-end gap-0.5">
                  {formatPrice(position.current_price)}
                  {position.price_kind ? <QuoteKindBadge kind={position.price_kind} className="px-1.5 py-0 text-[10px]" /> : null}
                </div>
              ) : (
                <span className="text-xs text-destructive">{position.quote_error}</span>
              )}
            </TableCell>
            <TableCell className="text-right">
              <PriceChange change={null} changePct={position.day_change_pct} hideAmount />
            </TableCell>
            <TableCell className="text-right">{formatMoney(position.market_value_twd)}</TableCell>
            <TableCell className={cn("text-right", signedValueClass(position.unrealized_pnl_twd))}>
              <p>{formatSignedMoney(position.unrealized_pnl_twd)}</p>
              <p className="text-xs">{formatPercent(position.unrealized_pnl_pct)}</p>
            </TableCell>
            <TableCell className={cn("text-right", signedValueClass(position.realized_pnl_twd))}>
              {formatSignedMoney(position.realized_pnl_twd)}
            </TableCell>
            <TableCell className="text-right">{formatPercent(position.weight_pct, { signed: false })}</TableCell>
            <TableCell className="text-right">
              <Button asChild size="sm" variant="ghost">
                <Link href={`/trading?symbol=${position.symbol}`} aria-label={`買賣 ${position.name}`}>
                  買賣
                </Link>
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

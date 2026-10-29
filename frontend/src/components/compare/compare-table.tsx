import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { PriceChange } from "@/components/stock/price-change";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate, formatPercent, formatPrice, formatVolume, signedValueClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ComparePoint, CompareStock } from "@/types/api";

export function CompareTable({ stocks, colorOf }: { stocks: CompareStock[]; colorOf: (symbol: string) => string }) {
  return (
    <Table data-testid="compare-table">
      <TableHeader>
        <TableRow>
          <TableHead>股票</TableHead>
          <TableHead className="text-right">最新價格</TableHead>
          <TableHead className="text-right">單日漲跌幅</TableHead>
          <TableHead className="text-right">成交量</TableHead>
          <TableHead className="text-right">區間累積報酬</TableHead>
          <TableHead className="text-right">最大回檔</TableHead>
          <TableHead className="text-right">期初 → 期末收盤</TableHead>
          <TableHead className="text-right">交易日（排除）</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="tabular">
        {stocks.map((stock) => (
          <TableRow key={stock.symbol}>
            <TableCell>
              <div className="flex items-center gap-2">
                <span className="inline-block h-0.5 w-3 shrink-0 rounded" style={{ backgroundColor: colorOf(stock.symbol) }} aria-hidden />
                <span className="font-medium">{stock.name}</span>
                <span className="font-mono text-xs text-muted-foreground">{stock.symbol}</span>
              </div>
            </TableCell>
            <TableCell className="text-right">
              <div className="flex items-center justify-end gap-1.5">
                {stock.quote_kind ? <QuoteKindBadge kind={stock.quote_kind} className="px-1.5 py-0 text-[10px]" /> : null}
                {formatPrice(stock.latest_price)}
                <span className="text-xs text-muted-foreground">{stock.currency}</span>
              </div>
            </TableCell>
            <TableCell className="text-right">
              <PriceChange change={null} changePct={stock.day_change_pct} hideAmount />
            </TableCell>
            <TableCell className="text-right">{formatVolume(stock.volume, stock.market)}</TableCell>
            <TableCell className={cn("text-right font-semibold", signedValueClass(stock.cumulative_return_pct))}>
              {formatPercent(stock.cumulative_return_pct)}
            </TableCell>
            <TableCell className="text-right">{formatPercent(stock.max_drawdown_pct)}</TableCell>
            <TableCell className="text-right text-muted-foreground">
              {formatPrice(stock.start_close)} → {formatPrice(stock.end_close)}
            </TableCell>
            <TableCell className="text-right text-muted-foreground">
              {stock.data_points}（{stock.excluded_dates}）
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/** 標準化指數的表格版本（無障礙與精確數值用），最新日期在最上面 */
export function NormalizedTable({ data, stocks }: { data: ComparePoint[]; stocks: CompareStock[] }) {
  return (
    <div className="max-h-80 overflow-y-auto rounded-md border">
      <Table>
        <TableHeader className="sticky top-0 bg-card">
          <TableRow>
            <TableHead>日期</TableHead>
            {stocks.map((stock) => (
              <TableHead key={stock.symbol} className="text-right">
                {stock.symbol}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody className="tabular">
          {[...data].reverse().map((point) => (
            <TableRow key={point.date}>
              <TableCell>{formatDate(point.date)}</TableCell>
              {stocks.map((stock) => (
                <TableCell key={stock.symbol} className="text-right">
                  {point.values[stock.symbol]?.toFixed(2)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

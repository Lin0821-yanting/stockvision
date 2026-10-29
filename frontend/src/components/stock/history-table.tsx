import { PriceChange } from "@/components/stock/price-change";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate, formatPrice, formatVolume } from "@/lib/format";
import type { HistoryResponse } from "@/types/api";

/** 走勢圖的表格版本（無障礙與精確數值用），最新日期在最上面 */
export function HistoryTable({ history }: { history: HistoryResponse }) {
  const rows = [...history.bars].reverse();
  return (
    <div className="max-h-80 overflow-y-auto rounded-md border">
      <Table>
        <TableHeader className="sticky top-0 bg-card">
          <TableRow>
            <TableHead>日期</TableHead>
            <TableHead className="text-right">開盤</TableHead>
            <TableHead className="text-right">最高</TableHead>
            <TableHead className="text-right">最低</TableHead>
            <TableHead className="text-right">收盤</TableHead>
            <TableHead className="text-right">漲跌幅</TableHead>
            <TableHead className="text-right">成交量</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="tabular">
          {rows.map((bar) => (
            <TableRow key={bar.date}>
              <TableCell>{formatDate(bar.date)}</TableCell>
              <TableCell className="text-right">{formatPrice(bar.open)}</TableCell>
              <TableCell className="text-right">{formatPrice(bar.high)}</TableCell>
              <TableCell className="text-right">{formatPrice(bar.low)}</TableCell>
              <TableCell className="text-right font-medium">{formatPrice(bar.close)}</TableCell>
              <TableCell className="text-right">
                <PriceChange change={bar.change} changePct={bar.change_pct} hideAmount />
              </TableCell>
              <TableCell className="text-right">{formatVolume(bar.volume, history.market)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

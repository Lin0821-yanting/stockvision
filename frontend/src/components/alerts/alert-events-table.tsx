import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDateTime, formatPrice } from "@/lib/format";
import type { AlertEvent } from "@/types/api";

export function AlertEventsTable({ events }: { events: AlertEvent[] }) {
  return (
    <Table data-testid="alert-events">
      <TableHeader>
        <TableRow>
          <TableHead>觸發時間</TableHead>
          <TableHead>股票</TableHead>
          <TableHead>條件</TableHead>
          <TableHead className="text-right">觸發價格</TableHead>
          <TableHead>價格來源</TableHead>
          <TableHead>通知</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="tabular">
        {events.map((event) => (
          <TableRow key={event.id}>
            <TableCell className="text-muted-foreground">{formatDateTime(event.triggered_at)}</TableCell>
            <TableCell>
              <span className="font-medium">{event.name}</span>
              <span className="ml-1.5 font-mono text-xs text-muted-foreground">{event.symbol}</span>
            </TableCell>
            <TableCell>
              {event.condition_label}
              {event.reference_low != null ? (
                <p className="text-xs text-muted-foreground">前 20 日最低收盤 {formatPrice(event.reference_low)}</p>
              ) : null}
            </TableCell>
            <TableCell className="text-right font-medium">{formatPrice(event.triggered_price)}</TableCell>
            <TableCell>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <QuoteKindBadge kind={event.price_kind} />
                {event.price_source}
              </div>
            </TableCell>
            <TableCell>
              {event.read_at ? (
                <span className="text-xs text-muted-foreground">已讀</span>
              ) : (
                <Badge className="border-primary/40 bg-primary/15 text-primary">未讀</Badge>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

"use client";

import Link from "next/link";

import { QuoteKindBadge } from "@/components/stock/data-source-badge";
import { PriceChange } from "@/components/stock/price-change";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatMarketCap, formatPrice, formatTime } from "@/lib/format";
import { MARKET_TIMEZONE } from "@/lib/market";
import type { MarketOverview } from "@/types/api";

import { PERIOD_LABEL, PeriodReturn } from "./overview-cards";

/** 走勢卡片的表格版本：同樣的數字，方便逐列比較或使用螢幕報讀器 */
export function OverviewTable({ data }: { data: MarketOverview }) {
  const timeZone = MARKET_TIMEZONE[data.market];
  return (
    <Table data-testid="overview-table">
      <TableHeader>
        <TableRow>
          <TableHead className="w-12">排名</TableHead>
          <TableHead>名稱</TableHead>
          <TableHead className="text-right">價格</TableHead>
          <TableHead className="text-right">今日漲跌</TableHead>
          <TableHead className="text-right">{PERIOD_LABEL[data.period]}</TableHead>
          <TableHead className="hidden text-right sm:table-cell">市值</TableHead>
          <TableHead className="hidden md:table-cell">資料</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {[...data.indices, ...data.stocks].map((item) => (
          <TableRow key={item.symbol} className={item.is_index ? "bg-muted/30" : undefined}>
            <TableCell className="text-muted-foreground tabular">{item.rank ?? "指數"}</TableCell>
            <TableCell>
              {/* 表格儲存格的 max-width 不可靠，寬度限制放在內層，太長的公司名稱以省略號截斷 */}
              <div className="flex max-w-44 min-w-0 items-baseline gap-1.5 sm:max-w-64">
                {item.is_index ? (
                  <span className="truncate font-medium">{item.name}</span>
                ) : (
                  <Link
                    href={`/market?symbol=${encodeURIComponent(item.symbol)}`}
                    className="truncate font-medium hover:underline"
                    title={item.name}
                  >
                    {item.name}
                  </Link>
                )}
                <span className="shrink-0 font-mono text-xs text-muted-foreground">{item.symbol}</span>
              </div>
            </TableCell>
            <TableCell className="text-right font-medium tabular">{formatPrice(item.quote?.price)}</TableCell>
            <TableCell className="text-right">
              <PriceChange change={item.quote?.change} changePct={item.quote?.change_pct} hideAmount />
            </TableCell>
            <TableCell className="text-right">
              <PeriodReturn value={item.period_return_pct} />
            </TableCell>
            <TableCell className="hidden text-right tabular sm:table-cell">
              {item.is_index ? "—" : formatMarketCap(item.market_cap, item.currency)}
            </TableCell>
            <TableCell className="hidden md:table-cell">
              {item.quote ? (
                <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <QuoteKindBadge kind={item.quote.kind} className="px-1.5 py-0 text-[10px]" />
                  {formatTime(item.quote.as_of, timeZone)}
                </span>
              ) : (
                <span className="text-xs text-destructive">{item.quote_error?.message ?? "報價暫時無法取得"}</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, type TooltipContentProps } from "recharts";

import { formatCompact, formatDate, formatPrice } from "@/lib/format";
import type { ComparePoint, CompareStock } from "@/types/api";

const AXIS_TICK = { fill: "var(--muted-foreground)", fontSize: 10 };

function CloseTooltip({ active, payload, symbol, currency }: TooltipContentProps & { symbol: string; currency: string }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as ComparePoint;
  return (
    <div className="rounded-md border bg-popover px-2.5 py-1.5 text-xs text-popover-foreground shadow-lg">
      <p className="text-muted-foreground">{formatDate(point.date)}</p>
      <p className="font-semibold tabular">
        {formatPrice(point.closes[symbol])} {currency}
      </p>
    </div>
  );
}

/** 各股收盤價小圖（small multiples）：每檔股票用自己的 Y 軸與幣別，取代誤導的雙軸圖 */
export function PriceMultiples({
  data,
  stocks,
  colorOf,
}: {
  data: ComparePoint[];
  stocks: CompareStock[];
  colorOf: (symbol: string) => string;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2" data-testid="price-multiples">
      {stocks.map((stock) => (
        <figure key={stock.symbol} className="min-w-0 rounded-lg border p-3">
          <figcaption className="mb-2 flex items-center gap-2 text-sm">
            <span className="inline-block h-0.5 w-3 shrink-0 rounded" style={{ backgroundColor: colorOf(stock.symbol) }} aria-hidden />
            <span className="min-w-0 flex-1 truncate font-medium">
              {stock.name} <span className="font-mono text-muted-foreground">{stock.symbol}</span>
            </span>
            <span className="text-xs text-muted-foreground">收盤價（{stock.currency}）</span>
          </figcaption>
          <div className="h-28">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <XAxis dataKey="date" hide />
                <YAxis
                  domain={["auto", "auto"]}
                  width={44}
                  tick={AXIS_TICK}
                  tickLine={false}
                  axisLine={false}
                  tickCount={3}
                  tickFormatter={(value: number) => formatCompact(value)}
                />
                <Tooltip
                  content={(props) => <CloseTooltip {...props} symbol={stock.symbol} currency={stock.currency} />}
                  cursor={{ stroke: "var(--muted-foreground)", strokeWidth: 1 }}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey={(point: ComparePoint) => point.closes[stock.symbol]}
                  stroke={colorOf(stock.symbol)}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: colorOf(stock.symbol), stroke: "var(--card)", strokeWidth: 2 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </figure>
      ))}
    </div>
  );
}

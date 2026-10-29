"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";

import { formatCompact, formatDate, formatPercent, formatPrice, formatShortDate, formatVolume, toneOf, TONE_ARROW, TONE_TEXT_CLASS } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { HistoryResponse, Market, PriceBar } from "@/types/api";

const AXIS_TICK = { fill: "var(--muted-foreground)", fontSize: 11 };
const Y_AXIS_WIDTH = 64;

function PriceTooltip({ active, payload, market }: TooltipContentProps & { market: Market }) {
  if (!active || !payload?.length) return null;
  const bar = payload[0].payload as PriceBar;
  const tone = toneOf(bar.change_pct);
  return (
    <div className="min-w-44 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-lg">
      <p className="text-muted-foreground">{formatDate(bar.date)}</p>
      <p className="mt-1 flex items-center gap-2">
        <span className="inline-block h-0.5 w-3 rounded bg-series-1" aria-hidden />
        <span className="text-sm font-semibold tabular">{formatPrice(bar.close)}</span>
        <span className="text-muted-foreground">收盤</span>
      </p>
      <p className={cn("mt-0.5 tabular", TONE_TEXT_CLASS[tone])}>
        {TONE_ARROW[tone]} {formatPercent(bar.change_pct)}
      </p>
      <dl className="mt-1.5 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 tabular">
        <dt className="text-muted-foreground">開</dt>
        <dd>{formatPrice(bar.open)}</dd>
        <dt className="text-muted-foreground">高</dt>
        <dd>{formatPrice(bar.high)}</dd>
        <dt className="text-muted-foreground">低</dt>
        <dd>{formatPrice(bar.low)}</dd>
        <dt className="text-muted-foreground">量</dt>
        <dd>{formatVolume(bar.volume, market)}</dd>
      </dl>
    </div>
  );
}

/** 歷史走勢：上方收盤價、下方成交量，兩張圖共用 X 軸與十字線（不使用雙 Y 軸） */
export function PriceHistoryChart({ history, dimmed = false }: { history: HistoryResponse; dimmed?: boolean }) {
  const bars = history.bars;
  const longRange = history.period === "6M" || history.period === "1Y";
  const dateTick = (value: string) => (longRange ? value.slice(0, 7).replace("-", "/") : formatShortDate(value));
  const volumeTick = (value: number) => formatCompact(history.market === "TW" ? value / 1000 : value);

  return (
    <div
      data-testid="price-chart"
      data-points={bars.length}
      className={cn("transition-opacity duration-300", dimmed && "opacity-50")}
      aria-label={`${history.name} ${history.period} 收盤價走勢圖`}
      role="img"
    >
      <div className="h-64 sm:h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={bars} syncId="price-history" margin={{ top: 8, right: 0, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
            <XAxis dataKey="date" hide />
            <YAxis
              orientation="right"
              domain={["auto", "auto"]}
              width={Y_AXIS_WIDTH}
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: number) => formatCompact(value)}
            />
            <Tooltip
              content={(props) => <PriceTooltip {...props} market={history.market} />}
              cursor={{ stroke: "var(--muted-foreground)", strokeWidth: 1 }}
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke="var(--series-1)"
              strokeWidth={2}
              fill="var(--series-1)"
              fillOpacity={0.1}
              dot={false}
              activeDot={{ r: 4, fill: "var(--series-1)", stroke: "var(--card)", strokeWidth: 2 }}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="h-24">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={bars} syncId="price-history" margin={{ top: 6, right: 0, bottom: 0, left: 0 }} barCategoryGap="15%">
            <XAxis
              dataKey="date"
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={{ stroke: "var(--chart-axis)" }}
              tickFormatter={dateTick}
              minTickGap={36}
            />
            <YAxis
              orientation="right"
              width={Y_AXIS_WIDTH}
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={false}
              tickCount={3}
              tickFormatter={volumeTick}
            />
            <Tooltip content={() => null} cursor={{ fill: "var(--muted)", fillOpacity: 0.5 }} isAnimationActive={false} />
            <Bar dataKey="volume" fill="var(--chart-muted)" radius={[2, 2, 0, 0]} maxBarSize={24} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-1 text-right text-xs text-muted-foreground">
        上：收盤價（{history.currency}）　下：成交量（{history.market === "TW" ? "張" : "股"}）
      </p>
    </div>
  );
}

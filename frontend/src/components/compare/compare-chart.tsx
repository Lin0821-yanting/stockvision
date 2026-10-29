"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";

import { formatDate, formatNumber, formatPrice, formatShortDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ComparePoint } from "@/types/api";

export type SeriesMeta = { symbol: string; name: string; color: string };

const AXIS_TICK = { fill: "var(--muted-foreground)", fontSize: 11 };

function CompareTooltip({ active, payload, series }: TooltipContentProps & { series: SeriesMeta[] }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as ComparePoint;
  const rows = [...series].sort((a, b) => (point.values[b.symbol] ?? 0) - (point.values[a.symbol] ?? 0));
  return (
    <div className="min-w-56 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-lg">
      <p className="mb-1 text-muted-foreground">{formatDate(point.date)}</p>
      {rows.map((item) => (
        <div key={item.symbol} className="flex items-center gap-2 py-0.5">
          <span className="inline-block h-0.5 w-3 shrink-0 rounded" style={{ backgroundColor: item.color }} aria-hidden />
          <span className="w-12 font-semibold tabular">{formatNumber(point.values[item.symbol], 2)}</span>
          <span className="min-w-0 flex-1 truncate text-muted-foreground">
            {item.name} {item.symbol}
          </span>
          <span className="tabular text-muted-foreground">{formatPrice(point.closes[item.symbol])}</span>
        </div>
      ))}
    </div>
  );
}

function EndLabel({ x, y, index, lastIndex, text }: { x?: number; y?: number; index?: number; lastIndex: number; text: string }) {
  if (index !== lastIndex || x == null || y == null) return <g />;
  // 文字使用一般文字色，顏色辨識交給線條本身與圖例
  return (
    <text x={x + 8} y={y} dy={4} fontSize={11} fill="var(--foreground)">
      {text}
    </text>
  );
}

/** 標準化走勢（共同起始日 = 100）。單一 Y 軸，不使用雙軸。 */
export function CompareChart({ data, series, dimmed = false }: { data: ComparePoint[]; series: SeriesMeta[]; dimmed?: boolean }) {
  const values = data.flatMap((point) => series.map((item) => point.values[item.symbol])).filter(Number.isFinite);
  const range = Math.max(...values) - Math.min(...values) || 1;
  const finals = series.map((item) => data.at(-1)?.values[item.symbol] ?? 0).sort((a, b) => a - b);
  // 線尾數值彼此夠遠才直接標註代號；太接近時只用圖例與 tooltip，避免標籤重疊
  const showEndLabels = finals.every((value, index) => index === 0 || value - finals[index - 1] >= range * 0.07);
  const lastIndex = data.length - 1;
  const longRange = data.length > 90;

  return (
    <div
      className={cn("h-80 transition-opacity duration-300", dimmed && "opacity-50")}
      data-testid="compare-chart"
      data-points={data.length}
      data-series={series.length}
      role="img"
      aria-label={`標準化走勢比較：${series.map((item) => item.symbol).join("、")}`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: showEndLabels ? 56 : 12, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="date"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={{ stroke: "var(--chart-axis)" }}
            tickFormatter={(value: string) => (longRange ? value.slice(0, 7).replace("-", "/") : formatShortDate(value))}
            minTickGap={36}
          />
          <YAxis
            domain={["auto", "auto"]}
            width={44}
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value: number) => String(Math.round(value))}
          />
          <ReferenceLine y={100} stroke="var(--chart-axis)" strokeWidth={1} />
          <Tooltip
            content={(props) => <CompareTooltip {...props} series={series} />}
            cursor={{ stroke: "var(--muted-foreground)", strokeWidth: 1 }}
            isAnimationActive={false}
          />
          {series.map((item) => (
            <Line
              key={item.symbol}
              type="monotone"
              name={item.symbol}
              dataKey={(point: ComparePoint) => point.values[item.symbol]}
              stroke={item.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: item.color, stroke: "var(--card)", strokeWidth: 2 }}
              isAnimationActive={false}
              label={showEndLabels ? <EndLabel lastIndex={lastIndex} text={item.symbol} /> : undefined}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

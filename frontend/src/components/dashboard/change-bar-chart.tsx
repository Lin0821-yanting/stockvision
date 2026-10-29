"use client";

import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";

import { formatPercent, formatPrice, toneOf, TONE_ARROW, TONE_TEXT_CLASS } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { WatchlistItem } from "@/types/api";

type Row = { symbol: string; name: string; label: string; pct: number; price: number | null; currency: string; kind: string };

const RADIUS = 4;

/** 長條只在「資料端」（離 0 較遠的一端）做 4px 圓角，基準線那端保持方角 */
function DataEndBar(props: { x?: number; y?: number; width?: number; height?: number; payload?: Row; fill?: string }) {
  const { x = 0, y = 0, width = 0, height = 0, payload, fill } = props;
  const left = Math.min(x, x + width);
  const w = Math.abs(width);
  if (w < 1 || height <= 0) return <g />;
  const r = Math.min(RADIUS, w, height / 2);
  const right = left + w;
  const positive = (payload?.pct ?? 0) >= 0;
  const d = positive
    ? `M${left},${y} H${right - r} Q${right},${y} ${right},${y + r} V${y + height - r} Q${right},${y + height} ${right - r},${y + height} H${left} Z`
    : `M${right},${y} H${left + r} Q${left},${y} ${left},${y + r} V${y + height - r} Q${left},${y + height} ${left + r},${y + height} H${right} Z`;
  return <path d={d} fill={fill} />;
}

function ValueLabel(props: { x?: number | string; y?: number | string; width?: number | string; height?: number | string; value?: number | string }) {
  const x = Number(props.x ?? 0);
  const y = Number(props.y ?? 0);
  const width = Number(props.width ?? 0);
  const height = Number(props.height ?? 0);
  const value = Number(props.value ?? 0);
  const tone = toneOf(value);
  const end = value >= 0 ? Math.max(x, x + width) + 6 : Math.min(x, x + width) - 6;
  return (
    <text x={end} y={y + height / 2} dy={4} fontSize={11} fill="var(--foreground)" textAnchor={value >= 0 ? "start" : "end"}>
      {TONE_ARROW[tone]} {formatPercent(value)}
    </text>
  );
}

function BarTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload as Row;
  const tone = toneOf(row.pct);
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-lg">
      <p className={cn("text-sm font-semibold tabular", TONE_TEXT_CLASS[tone])}>
        {TONE_ARROW[tone]} {formatPercent(row.pct)}
      </p>
      <p className="text-muted-foreground">
        {row.name} {row.symbol}
      </p>
      <p className="tabular">
        {formatPrice(row.price)} {row.currency}（{row.kind === "realtime" ? "盤中" : "收盤"}）
      </p>
    </div>
  );
}

/** 自選股漲跌幅：以 0 為基準的水平長條（右漲左跌＋▲▼標示，不只靠紅綠區分） */
export function ChangeBarChart({ items }: { items: WatchlistItem[] }) {
  const rows: Row[] = items
    .filter((item) => item.quote?.change_pct != null)
    .map((item) => ({
      symbol: item.symbol,
      name: item.name,
      label: item.symbol,
      pct: item.quote!.change_pct!,
      price: item.quote!.price,
      currency: item.currency,
      kind: item.quote!.kind,
    }))
    .sort((a, b) => b.pct - a.pct);

  if (!rows.length) return <p className="text-sm text-muted-foreground">自選股取得報價後會顯示漲跌幅。</p>;

  const extent = Math.max(0.5, ...rows.map((row) => Math.abs(row.pct)));
  const height = Math.max(120, rows.length * 34 + 24);

  return (
    <div style={{ height }} data-testid="change-chart" data-bars={rows.length} role="img" aria-label="自選股今日漲跌幅長條圖">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 8, bottom: 4, left: 0 }} barCategoryGap={8}>
          <XAxis type="number" domain={[-extent * 1.6, extent * 1.6]} hide />
          <YAxis
            type="category"
            dataKey="label"
            width={52}
            tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <ReferenceLine x={0} stroke="var(--chart-axis)" strokeWidth={1} />
          <Tooltip content={(props) => <BarTooltip {...props} />} cursor={{ fill: "var(--muted)", fillOpacity: 0.4 }} isAnimationActive={false} />
          <Bar dataKey="pct" shape={<DataEndBar />} maxBarSize={20} isAnimationActive={false}>
            {rows.map((row) => (
              <Cell key={row.symbol} fill={row.pct >= 0 ? "var(--chart-up)" : "var(--chart-down)"} />
            ))}
            <LabelList dataKey="pct" content={<ValueLabel />} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

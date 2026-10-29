"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, YAxis, type TooltipContentProps } from "recharts";

import { formatDate, formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { SparkPoint } from "@/types/api";

function SparkTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as SparkPoint;
  return (
    <div className="rounded-md border bg-popover px-2 py-1 text-xs text-popover-foreground shadow-lg">
      <p className="text-muted-foreground">{formatDate(point.date)}</p>
      <p className="flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-2.5 rounded bg-series-1" aria-hidden />
        <span className="font-semibold tabular">{formatPrice(point.close)}</span>
        <span className="text-muted-foreground">收盤</span>
      </p>
    </div>
  );
}

/** 小走勢圖：單一序列使用 series-1，每張圖用自己的價格刻度；滑過時顯示日期與收盤價 */
export function Sparkline({ points, label, className }: { points: SparkPoint[]; label: string; className?: string }) {
  if (points.length < 2) {
    return (
      <div className={cn("flex items-center justify-center rounded-md bg-muted/30 text-xs text-muted-foreground", className)}>
        走勢資料不足
      </div>
    );
  }
  return (
    <div className={className} role="img" aria-label={label} data-testid="sparkline" data-points={points.length}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 4, right: 2, bottom: 2, left: 2 }}>
          <YAxis hide domain={["dataMin", "dataMax"]} />
          <Tooltip
            content={(props) => <SparkTooltip {...props} />}
            cursor={{ stroke: "var(--muted-foreground)", strokeWidth: 1 }}
            isAnimationActive={false}
            allowEscapeViewBox={{ x: false, y: true }}
          />
          <Area
            type="monotone"
            dataKey="close"
            stroke="var(--series-1)"
            strokeWidth={2}
            fill="var(--series-1)"
            fillOpacity={0.08}
            dot={false}
            activeDot={{ r: 3, fill: "var(--series-1)", stroke: "var(--card)", strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

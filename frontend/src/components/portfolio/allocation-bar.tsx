import { formatMoney, formatPercent } from "@/lib/format";
import type { Portfolio } from "@/types/api";

const SLOTS = 6;
const SERIES = Array.from({ length: SLOTS }, (_, index) => `var(--series-${index + 1})`);
const OTHER_COLOR = "var(--chart-muted)";

type Segment = { key: string; label: string; value: number; color: string };

/**
 * 持股配置：100% 水平堆疊長條＋圖例表。
 * 顏色依持股建立順序固定分配（不依市值排名），漲跌時顏色不會互換；超過 6 檔併入「其他」。
 */
export function AllocationBar({ portfolio }: { portfolio: Portfolio }) {
  const valued = portfolio.positions.filter((position) => (position.market_value_twd ?? 0) > 0);
  const total = valued.reduce((sum, position) => sum + (position.market_value_twd ?? 0), 0);
  if (!valued.length || total <= 0) {
    return <p className="text-sm text-muted-foreground">目前沒有持股，買進股票後會顯示配置比例。</p>;
  }

  const segments: Segment[] = valued.slice(0, SLOTS).map((position, index) => ({
    key: position.symbol,
    label: `${position.name} ${position.symbol}`,
    value: position.market_value_twd ?? 0,
    color: SERIES[index],
  }));
  const rest = valued.slice(SLOTS);
  if (rest.length) {
    segments.push({
      key: "other",
      label: `其他 ${rest.length} 檔`,
      value: rest.reduce((sum, position) => sum + (position.market_value_twd ?? 0), 0),
      color: OTHER_COLOR,
    });
  }
  const cashShare = (portfolio.cash_twd / portfolio.total_assets_twd) * 100;

  return (
    <div className="space-y-4" data-testid="allocation-bar">
      <div className="flex h-3 w-full gap-0.5 overflow-hidden rounded-full" role="img" aria-label="持股配置比例">
        {segments.map((segment) => (
          <div
            key={segment.key}
            className="h-full first:rounded-l-full last:rounded-r-full"
            style={{ width: `${(segment.value / total) * 100}%`, backgroundColor: segment.color }}
            title={`${segment.label}：${formatPercent((segment.value / total) * 100, { signed: false })}`}
          />
        ))}
      </div>
      <ul className="grid gap-2 text-sm">
        {segments.map((segment) => (
          <li key={segment.key} className="flex items-center gap-2">
            <span className="size-2.5 shrink-0 rounded-sm" style={{ backgroundColor: segment.color }} aria-hidden />
            <span className="min-w-0 flex-1 truncate">{segment.label}</span>
            <span className="tabular text-muted-foreground">{formatMoney(segment.value)}</span>
            <span className="w-16 text-right font-medium tabular">
              {formatPercent((segment.value / total) * 100, { signed: false })}
            </span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-muted-foreground">
        以上為股票部位的配置；現金 {formatMoney(portfolio.cash_twd)} 占總資產 {formatPercent(cashShare, { signed: false })}。
      </p>
    </div>
  );
}

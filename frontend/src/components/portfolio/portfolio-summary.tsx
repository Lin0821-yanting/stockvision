import { TriangleAlert } from "lucide-react";

import { StatCard } from "@/components/common/stat-card";
import { formatMoney, formatPercent, formatSignedMoney, signedValueClass, toneOf } from "@/lib/format";
import type { Portfolio } from "@/types/api";

export function PortfolioSummary({ portfolio }: { portfolio: Portfolio }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 2xl:grid-cols-6" data-testid="portfolio-summary">
        <StatCard
          testId="stat-total-assets"
          label="總資產"
          value={formatMoney(portfolio.total_assets_twd)}
          delta={`${formatSignedMoney(portfolio.total_pnl_twd)}（${formatPercent(portfolio.roi_pct)}）`}
          tone={toneOf(portfolio.total_pnl_twd)}
        />
        <StatCard
          testId="stat-cash"
          label="現金餘額"
          value={formatMoney(portfolio.cash_twd)}
          hint={`初始資金 ${formatMoney(portfolio.account.initial_cash)}`}
        />
        <StatCard
          testId="stat-market-value"
          label="持股市值"
          value={formatMoney(portfolio.market_value_twd)}
          hint={`持股成本 ${formatMoney(portfolio.cost_basis_twd)}`}
        />
        <StatCard
          label="未實現損益"
          value={formatSignedMoney(portfolio.unrealized_pnl_twd)}
          valueClassName={signedValueClass(portfolio.unrealized_pnl_twd)}
          hint="持股目前市值 − 台幣成本"
        />
        <StatCard
          label="已實現損益"
          value={formatSignedMoney(portfolio.realized_pnl_twd)}
          valueClassName={signedValueClass(portfolio.realized_pnl_twd)}
          hint={`第 ${portfolio.account.cycle} 輪賣出累計`}
        />
        <StatCard
          testId="stat-roi"
          label="投資報酬率"
          value={formatPercent(portfolio.roi_pct)}
          valueClassName={signedValueClass(portfolio.roi_pct)}
          hint="（總資產 − 初始資金）÷ 初始資金"
        />
      </div>
      {portfolio.warnings.length ? (
        <div role="status" className="flex gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-amber-400" aria-hidden />
          <ul className="space-y-0.5">
            {portfolio.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

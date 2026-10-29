"use client";

import { useRouter } from "next/navigation";

import { StockSearch } from "@/components/stock/stock-search";

export function GlobalSearch({ className }: { className?: string }) {
  const router = useRouter();
  return (
    <StockSearch
      className={className}
      placeholder="搜尋股票：2330、台積電、AAPL"
      onSelect={(stock) => router.push(`/market?symbol=${encodeURIComponent(stock.symbol)}`)}
    />
  );
}

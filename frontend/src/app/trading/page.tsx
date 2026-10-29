import type { Metadata } from "next";
import { Suspense } from "react";

import { TradingSkeleton, TradingView } from "@/components/trading/trading-view";

export const metadata: Metadata = { title: "模擬下單" };

export default function TradingPage() {
  return (
    <Suspense fallback={<TradingSkeleton />}>
      <TradingView />
    </Suspense>
  );
}

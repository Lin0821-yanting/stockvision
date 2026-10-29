import type { Metadata } from "next";
import { Suspense } from "react";

import { RequireAuth } from "@/components/auth/require-auth";
import { TradingSkeleton, TradingView } from "@/components/trading/trading-view";

export const metadata: Metadata = { title: "模擬下單" };

export default function TradingPage() {
  return (
    <Suspense fallback={<TradingSkeleton />}>
      <RequireAuth title="模擬下單" description="每個帳號都有自己的 NT$1,000,000 模擬資金，交易紀錄與持股彼此獨立。">
        <TradingView />
      </RequireAuth>
    </Suspense>
  );
}

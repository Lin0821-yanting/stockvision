import type { Metadata } from "next";
import { Suspense } from "react";

import { CardSkeleton } from "@/components/common/states";
import { MarketView } from "@/components/market/market-view";

export const metadata: Metadata = { title: "股票看盤" };

export default function MarketPage() {
  return (
    <Suspense fallback={<CardSkeleton rows={6} />}>
      <MarketView />
    </Suspense>
  );
}

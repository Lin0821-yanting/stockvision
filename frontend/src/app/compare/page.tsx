import type { Metadata } from "next";
import { Suspense } from "react";

import { CardSkeleton } from "@/components/common/states";
import { CompareView } from "@/components/compare/compare-view";

export const metadata: Metadata = { title: "股票比較" };

export default function ComparePage() {
  return (
    <Suspense fallback={<CardSkeleton rows={6} />}>
      <CompareView />
    </Suspense>
  );
}

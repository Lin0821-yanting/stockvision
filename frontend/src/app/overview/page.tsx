import type { Metadata } from "next";
import { Suspense } from "react";

import { CardSkeleton } from "@/components/common/states";
import { OverviewView } from "@/components/overview/overview-view";

export const metadata: Metadata = { title: "大盤總覽" };

export default function OverviewPage() {
  return (
    <Suspense fallback={<CardSkeleton rows={6} />}>
      <OverviewView />
    </Suspense>
  );
}

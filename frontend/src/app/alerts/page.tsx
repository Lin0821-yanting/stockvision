import type { Metadata } from "next";
import { Suspense } from "react";

import { AlertsView } from "@/components/alerts/alerts-view";
import { CardSkeleton } from "@/components/common/states";

export const metadata: Metadata = { title: "價格提醒" };

export default function AlertsPage() {
  return (
    <Suspense fallback={<CardSkeleton rows={6} />}>
      <AlertsView />
    </Suspense>
  );
}

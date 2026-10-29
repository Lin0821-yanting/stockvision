import { Suspense } from "react";

import { CardSkeleton } from "@/components/common/states";
import { DashboardView } from "@/components/dashboard/dashboard-view";

export default function DashboardPage() {
  return (
    <Suspense fallback={<CardSkeleton rows={6} />}>
      <DashboardView />
    </Suspense>
  );
}

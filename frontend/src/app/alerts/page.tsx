import type { Metadata } from "next";
import { Suspense } from "react";

import { RequireAuth } from "@/components/auth/require-auth";
import { AlertsView } from "@/components/alerts/alerts-view";
import { CardSkeleton } from "@/components/common/states";

export const metadata: Metadata = { title: "價格提醒" };

export default function AlertsPage() {
  return (
    <Suspense fallback={<CardSkeleton rows={6} />}>
      <RequireAuth title="價格提醒" description="登入後可以設定到價提醒與 20 日新低提醒，觸發時會出現在站內通知。">
        <AlertsView />
      </RequireAuth>
    </Suspense>
  );
}

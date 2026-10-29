import type { Metadata } from "next";
import { Suspense } from "react";

import { RequireAuth } from "@/components/auth/require-auth";
import { CardSkeleton } from "@/components/common/states";
import { PortfolioView } from "@/components/portfolio/portfolio-view";

export const metadata: Metadata = { title: "投資組合" };

export default function PortfolioPage() {
  return (
    <Suspense fallback={<CardSkeleton rows={6} />}>
      <RequireAuth title="投資組合" description="登入後可以查看自己的持股、損益、資產配置與完整交易紀錄。">
        <PortfolioView />
      </RequireAuth>
    </Suspense>
  );
}

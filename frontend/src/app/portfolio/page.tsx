import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";
import { PageHeader } from "@/components/common/page-header";

export const metadata: Metadata = { title: "投資組合" };

export default function PortfolioPage() {
  return (
    <>
      <PageHeader title="投資組合" description="持股、損益、總資產與完整交易紀錄" />
      <ComingSoon feature="投資組合" />
    </>
  );
}

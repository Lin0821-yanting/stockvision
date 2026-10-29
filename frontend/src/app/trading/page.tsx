import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";
import { PageHeader } from "@/components/common/page-header";

export const metadata: Metadata = { title: "模擬下單" };

export default function TradingPage() {
  return (
    <>
      <PageHeader title="模擬下單" description="使用 NT$1,000,000 虛擬資金練習買賣台股與美股" />
      <ComingSoon feature="模擬下單" />
    </>
  );
}

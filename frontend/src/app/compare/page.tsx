import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";
import { PageHeader } from "@/components/common/page-header";

export const metadata: Metadata = { title: "股票比較" };

export default function ComparePage() {
  return (
    <>
      <PageHeader title="股票比較" description="選擇 2 至 4 檔股票，比較標準化走勢與區間報酬" />
      <ComingSoon feature="股票比較" />
    </>
  );
}

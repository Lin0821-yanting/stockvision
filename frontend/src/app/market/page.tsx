import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";
import { PageHeader } from "@/components/common/page-header";

export const metadata: Metadata = { title: "股票看盤" };

export default function MarketPage() {
  return (
    <>
      <PageHeader title="股票看盤" description="搜尋台股、美股，查看盤中報價與歷史走勢" />
      <ComingSoon feature="股票看盤" />
    </>
  );
}

import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";
import { PageHeader } from "@/components/common/page-header";

export const metadata: Metadata = { title: "價格提醒" };

export default function AlertsPage() {
  return (
    <>
      <PageHeader title="價格提醒" description="設定低價、高價與 20 日新低提醒" />
      <ComingSoon feature="價格提醒" />
    </>
  );
}

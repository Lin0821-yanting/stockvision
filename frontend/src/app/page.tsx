import { ComingSoon } from "@/components/common/coming-soon";
import { PageHeader } from "@/components/common/page-header";

export default function DashboardPage() {
  return (
    <>
      <PageHeader title="投資總覽" description="自選股、模擬投資組合與價格提醒的整合首頁" />
      <ComingSoon feature="投資總覽" />
    </>
  );
}

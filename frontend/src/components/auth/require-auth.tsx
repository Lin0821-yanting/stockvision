"use client";

import { PageHeader } from "@/components/common/page-header";
import { CardSkeleton, ErrorState } from "@/components/common/states";
import { useAuth } from "@/hooks/use-auth";

import { LoginPromptCard } from "./login-prompt";

/** 包住需要登入的頁面：未登入時顯示登入提示，不會送出任何個人資料的請求 */
export function RequireAuth({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const { user, isLoading, error, retry } = useAuth();

  if (user) return children;
  if (isLoading) return <CardSkeleton rows={6} />;
  return (
    <>
      <PageHeader title={title} />
      {error ? (
        <ErrorState error={error} title="無法確認登入狀態" onRetry={retry} />
      ) : (
        <LoginPromptCard title="請先登入" description={description} />
      )}
    </>
  );
}

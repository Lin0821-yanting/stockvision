import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthView } from "@/components/auth/auth-view";
import { CardSkeleton } from "@/components/common/states";

export const metadata: Metadata = { title: "登入／註冊" };

export default function LoginPage() {
  return (
    <Suspense fallback={<CardSkeleton rows={5} className="mx-auto max-w-md" />}>
      <AuthView />
    </Suspense>
  );
}

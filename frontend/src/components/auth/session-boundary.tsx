"use client";

import { Fragment, useState } from "react";

import { useAuth } from "@/hooks/use-auth";

/**
 * 切換帳號或登出時重新掛載整個畫面，清掉上一位使用者留在元件裡的狀態（表單內容、保留的舊資料）。
 * 第一次確認登入狀態時不重新掛載，避免頁面載入後閃一下。
 */
export function SessionBoundary({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const identity = isLoading ? undefined : (user?.id ?? null);
  const [state, setState] = useState({ identity, generation: 0 });

  if (identity !== undefined && identity !== state.identity) {
    setState({ identity, generation: state.identity === undefined ? state.generation : state.generation + 1 });
  }

  return <Fragment key={state.generation}>{children}</Fragment>;
}

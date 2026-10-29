"use client";

import { mutate, SWRConfig } from "swr";

import { SessionBoundary } from "@/components/auth/session-boundary";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AUTH_KEY } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        dedupingInterval: 2000,
        // 4xx（例如找不到代號）重試也不會成功；網路與 5xx 錯誤最多再試兩次
        onErrorRetry: (error, _key, _config, revalidate, { retryCount }) => {
          if (error instanceof ApiError && error.status >= 400 && error.status < 500) return;
          if (retryCount >= 2) return;
          setTimeout(() => revalidate({ retryCount }), 4000);
        },
        // 登入逾期或在其他分頁登出：重新確認登入狀態，畫面會改成登入提示
        onError: (error, key) => {
          if (error instanceof ApiError && error.status === 401 && key !== AUTH_KEY) void mutate(AUTH_KEY);
        },
      }}
    >
      <TooltipProvider>
        <SessionBoundary>{children}</SessionBoundary>
      </TooltipProvider>
    </SWRConfig>
  );
}

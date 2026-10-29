"use client";

import { SWRConfig } from "swr";

import { TooltipProvider } from "@/components/ui/tooltip";
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
      }}
    >
      <TooltipProvider>{children}</TooltipProvider>
    </SWRConfig>
  );
}

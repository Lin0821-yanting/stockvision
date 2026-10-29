"use client";

import { usePathname, useSearchParams } from "next/navigation";

export type AuthMode = "login" | "register";

/** 組出登入頁網址；登入後會依 next 參數回到目前的頁面（需放在 Suspense 內） */
export function useLoginHref(mode: AuthMode = "login"): string {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  return buildLoginHref(mode, pathname, searchParams.toString());
}

export function buildLoginHref(mode: AuthMode, pathname: string, query = ""): string {
  const params = new URLSearchParams();
  if (mode === "register") params.set("mode", "register");
  if (pathname !== "/" && pathname !== "/login") params.set("next", query ? `${pathname}?${query}` : pathname);
  const search = params.toString();
  return search ? `/login?${search}` : "/login";
}

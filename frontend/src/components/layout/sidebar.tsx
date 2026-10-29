"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Lock } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

import { NAV_ITEMS, isActivePath } from "./nav-items";

export function Brand() {
  return (
    <Link href="/" className="flex items-center gap-2.5" aria-label="StockVision 首頁">
      <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <svg viewBox="0 0 32 32" className="size-5" aria-hidden="true">
          <path
            d="M5 22l7-7 4 4 10-10"
            fill="none"
            stroke="currentColor"
            strokeWidth="3.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="flex flex-col leading-tight">
        <span className="text-base font-semibold tracking-tight">StockVision</span>
        <span className="text-xs text-muted-foreground">台美股看盤・模擬投資</span>
      </span>
    </Link>
  );
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, isLoading } = useAuth();
  const locked = !user && !isLoading;

  return (
    <nav className="flex flex-col gap-1" aria-label="主要導覽">
      {NAV_ITEMS.map((item) => {
        const active = isActivePath(pathname, item.href);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              active
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
            )}
          >
            <Icon className={cn("size-4", active && "text-primary")} />
            <span className="font-medium">{item.label}</span>
            {locked && item.requiresAuth ? (
              <>
                <Lock className="size-3.5 text-muted-foreground/70" aria-hidden />
                <span className="sr-only">（需要登入）</span>
              </>
            ) : null}
            <span className="ml-auto text-xs text-muted-foreground/70">{item.description}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden border-r border-sidebar-border bg-sidebar lg:block lg:w-64 lg:shrink-0">
      <div className="sticky top-0 flex h-screen flex-col gap-6 p-4">
        <Brand />
        <SidebarNav />
        <p className="mt-auto rounded-lg border border-sidebar-border p-3 text-xs leading-relaxed text-muted-foreground">
          資料來源：FinMind、臺灣證券交易所、櫃買中心、Finnhub。所有價格皆標示資料時間；模擬交易不代表真實成交。
        </p>
      </div>
    </aside>
  );
}

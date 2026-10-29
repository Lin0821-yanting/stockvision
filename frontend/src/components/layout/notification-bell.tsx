"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { Bell, BellRing, CheckCheck } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNotifications, useRefreshAlerts } from "@/hooks/use-alerts";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { errorMessage } from "@/services/api-client";
import { notificationsApi } from "@/services/alerts";

/** 站內通知：鈴鐺顯示未讀數；有新的提醒觸發時跳出 toast */
export function NotificationBell() {
  const { data } = useNotifications();
  const refresh = useRefreshAlerts();
  const seen = useRef<Set<number> | null>(null);

  useEffect(() => {
    if (!data) return;
    const unread = data.items.filter((item) => !item.read_at);
    if (seen.current === null) {
      // 第一次載入只記錄既有通知，不重複跳出舊的 toast
      seen.current = new Set(data.items.map((item) => item.id));
      return;
    }
    for (const item of unread) {
      if (!seen.current.has(item.id)) {
        toast.warning(`價格提醒：${item.name}（${item.symbol}）`, { description: item.message, duration: 10_000 });
      }
    }
    for (const item of data.items) seen.current.add(item.id);
  }, [data]);

  async function markAllRead() {
    try {
      await notificationsApi.readAll();
      await refresh();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  async function markRead(id: number) {
    try {
      await notificationsApi.read(id);
      await refresh();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  const unreadCount = data?.unread_count ?? 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label={`站內通知，${unreadCount} 則未讀`} data-testid="notification-bell">
          {unreadCount ? <BellRing /> : <Bell />}
          {unreadCount ? (
            <span className="absolute -top-0.5 -right-0.5 flex min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          站內通知
          {unreadCount ? (
            <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={markAllRead}>
              <CheckCheck />
              全部已讀
            </Button>
          ) : null}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {data?.items.length ? (
          data.items.slice(0, 8).map((item) => (
            <DropdownMenuItem
              key={item.id}
              onSelect={() => {
                if (!item.read_at) void markRead(item.id);
              }}
              className="flex flex-col items-start gap-0.5 py-2"
            >
              <span className={cn("flex w-full items-center gap-2 text-sm", !item.read_at && "font-medium")}>
                {!item.read_at ? <span className="size-1.5 shrink-0 rounded-full bg-primary" aria-label="未讀" /> : null}
                {item.name}（{item.symbol}）
                <span className="ml-auto text-xs font-normal text-muted-foreground">{formatDateTime(item.triggered_at)}</span>
              </span>
              <span className="text-xs whitespace-normal text-muted-foreground">{item.message}</span>
            </DropdownMenuItem>
          ))
        ) : (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">目前沒有通知</p>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/alerts" className="justify-center text-sm">
            管理價格提醒
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

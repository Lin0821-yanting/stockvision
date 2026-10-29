"use client";

import Link from "next/link";
import { BellRing, CircleUserRound, LogIn, LogOut, UserPlus, Wallet } from "lucide-react";
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
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import { useLoginHref } from "@/hooks/use-login-href";
import { errorMessage } from "@/services/api-client";

import { NotificationBell } from "./notification-bell";

export function UserMenuSkeleton() {
  return <Skeleton className="h-8 w-20" />;
}

/** 頂欄右側：已登入時顯示通知鈴鐺與使用者選單，未登入時顯示登入／註冊 */
export function UserMenu() {
  const { user, isLoading, logout } = useAuth();
  const loginHref = useLoginHref("login");
  const registerHref = useLoginHref("register");

  if (isLoading) return <UserMenuSkeleton />;

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Button asChild variant="outline" size="sm">
          <Link href={loginHref} data-testid="login-link">
            <LogIn />
            登入
          </Link>
        </Button>
        <Button asChild size="sm" className="hidden sm:inline-flex">
          <Link href={registerHref}>
            <UserPlus />
            註冊
          </Link>
        </Button>
      </div>
    );
  }

  async function signOut() {
    try {
      await logout();
      toast.success("已登出");
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  return (
    <>
      <NotificationBell />
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="max-w-44 px-2" aria-label={`使用者選單：${user.display_name}`} data-testid="user-menu">
            <CircleUserRound />
            <span className="hidden truncate sm:inline">{user.display_name}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="flex flex-col gap-0.5">
            <span className="truncate">{user.display_name}</span>
            <span className="truncate text-xs font-normal text-muted-foreground">@{user.username}</span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href="/portfolio">
              <Wallet />
              我的投資組合
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/alerts">
              <BellRing />
              我的價格提醒
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={() => void signOut()} data-testid="logout">
            <LogOut />
            登出
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}

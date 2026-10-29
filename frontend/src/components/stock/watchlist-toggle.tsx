"use client";

import { useState } from "react";
import Link from "next/link";
import { Star, StarOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useLoginHref } from "@/hooks/use-login-href";
import { useWatchlist } from "@/hooks/use-watchlist";

export function WatchlistToggle({ symbol }: { symbol: string }) {
  const { user, isLoading } = useAuth();
  const loginHref = useLoginHref("login");
  const { has, add, remove, data } = useWatchlist();
  const [pending, setPending] = useState(false);
  const inList = has(symbol);

  async function toggle() {
    setPending(true);
    await (inList ? remove(symbol) : add(symbol));
    setPending(false);
  }

  if (!user && !isLoading) {
    return (
      <Button asChild variant="outline" size="sm" data-testid="watchlist-toggle">
        <Link href={loginHref}>
          <Star />
          登入後加入自選
        </Link>
      </Button>
    );
  }

  return (
    <Button
      variant={inList ? "secondary" : "outline"}
      size="sm"
      onClick={toggle}
      disabled={pending || !data}
      aria-pressed={inList}
      data-testid="watchlist-toggle"
    >
      {inList ? <StarOff /> : <Star />}
      {inList ? "移除自選" : "加入自選"}
    </Button>
  );
}

"use client";

import { useState } from "react";
import { Star, StarOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useWatchlist } from "@/hooks/use-watchlist";

export function WatchlistToggle({ symbol }: { symbol: string }) {
  const { has, add, remove, data } = useWatchlist();
  const [pending, setPending] = useState(false);
  const inList = has(symbol);

  async function toggle() {
    setPending(true);
    await (inList ? remove(symbol) : add(symbol));
    setPending(false);
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

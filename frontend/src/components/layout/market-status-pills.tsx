"use client";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useMarketStatus } from "@/hooks/use-market";
import { cn } from "@/lib/utils";

export function MarketStatusPills({ className }: { className?: string }) {
  const { data } = useMarketStatus();
  if (!data) return null;

  return (
    <div className={cn("flex items-center gap-2", className)} data-testid="market-status">
      {data.markets.map((session) => (
        <Tooltip key={session.market}>
          <TooltipTrigger asChild>
            <span
              tabIndex={0}
              className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs whitespace-nowrap"
            >
              <span
                aria-hidden
                className={cn("size-2 rounded-full", session.is_open ? "animate-pulse bg-primary" : "bg-muted-foreground/50")}
              />
              {session.name} {session.label}
            </span>
          </TooltipTrigger>
          <TooltipContent className="max-w-64">
            {session.session}，台北時間 {session.session_taipei}。{session.note}
          </TooltipContent>
        </Tooltip>
      ))}
    </div>
  );
}

"use client";

import { useId, useState } from "react";
import { LoaderCircle, Search } from "lucide-react";
import useSWR from "swr";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useDebounce } from "@/hooks/use-debounce";
import { MARKET_LABEL, exchangeLabel } from "@/lib/market";
import { cn } from "@/lib/utils";
import { errorMessage } from "@/services/api-client";
import { stocksApi } from "@/services/stocks";
import type { StockInfo } from "@/types/api";

export function StockSearch({
  onSelect,
  placeholder = "搜尋代號或名稱，例如 2330、台積電、AAPL",
  className,
  autoFocus,
}: {
  onSelect: (stock: StockInfo) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const listId = useId();
  const term = useDebounce(query.trim(), 250);

  const { data, error, isLoading } = useSWR(term ? ["search", term] : null, () => stocksApi.search(term), {
    keepPreviousData: true,
    revalidateOnFocus: false,
  });
  const results = term ? (data?.results ?? []) : [];
  const showList = open && query.trim().length > 0;

  function choose(stock: StockInfo) {
    onSelect(stock);
    setQuery("");
    setOpen(false);
    setActive(0);
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActive((index) => Math.min(index + 1, Math.max(results.length - 1, 0)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter") {
      const stock = results[active];
      if (stock) {
        event.preventDefault();
        choose(stock);
      }
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className={cn("relative w-full", className)}>
      <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
      <Input
        type="search"
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-label="搜尋股票"
        autoFocus={autoFocus}
        value={query}
        placeholder={placeholder}
        className="pl-9"
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          setActive(0);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={onKeyDown}
      />
      {isLoading && term ? (
        <LoaderCircle className="absolute top-1/2 right-3 size-4 -translate-y-1/2 animate-spin text-muted-foreground" aria-label="搜尋中" />
      ) : null}

      {showList ? (
        <ul
          id={listId}
          role="listbox"
          className="absolute top-full right-0 left-0 z-50 mt-1 max-h-80 overflow-y-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-lg"
        >
          {error ? (
            <li className="px-3 py-2 text-sm text-destructive">{errorMessage(error)}</li>
          ) : !term || (isLoading && !data) ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">搜尋中…</li>
          ) : results.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">找不到符合「{term}」的股票</li>
          ) : (
            results.map((stock, index) => (
              <li
                key={`${stock.market}-${stock.symbol}`}
                role="option"
                aria-selected={index === active}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-sm px-3 py-2 text-sm",
                  index === active ? "bg-accent text-accent-foreground" : "hover:bg-accent/60",
                )}
                onMouseEnter={() => setActive(index)}
                onMouseDown={(event) => {
                  event.preventDefault();
                  choose(stock);
                }}
              >
                <span className="w-16 shrink-0 font-mono font-medium">{stock.symbol}</span>
                <span className="min-w-0 flex-1 truncate">{stock.name}</span>
                <Badge variant="outline" className="shrink-0 text-muted-foreground">
                  {stock.market === "TW" ? exchangeLabel(stock.exchange) : MARKET_LABEL.US}
                </Badge>
              </li>
            ))
          )}
          {data?.warnings.length ? (
            <li className="border-t px-3 py-2 text-xs text-muted-foreground">{data.warnings.join("；")}</li>
          ) : null}
        </ul>
      ) : null}
    </div>
  );
}

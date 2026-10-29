"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { MarketStatusPills } from "@/components/layout/market-status-pills";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MARKET_LABEL } from "@/lib/market";
import type { Market, Period } from "@/types/api";

import { MarketPanel, type OverviewView as View } from "./market-panel";
import { MarketSlider, PageToggle } from "./market-slider";

const MARKETS: Market[] = ["TW", "US"];
const PERIODS: { value: Period; label: string }[] = [
  { value: "1M", label: "1 個月" },
  { value: "3M", label: "3 個月" },
  { value: "6M", label: "6 個月" },
  { value: "1Y", label: "1 年" },
];

function parseMarket(value: string | null): Market {
  return value === "US" ? "US" : "TW";
}

function parsePeriod(value: string | null): Period {
  return PERIODS.some((item) => item.value === value) ? (value as Period) : "1M";
}

/** 不經過伺服器直接更新網址（Next.js 會同步 useSearchParams），切換時動畫不會卡住 */
function writeUrl(market: Market, period: Period) {
  const params = new URLSearchParams(window.location.search);
  if (market === "TW") params.delete("market");
  else params.set("market", market);
  if (period === "1M") params.delete("period");
  else params.set("period", period);
  const search = params.toString();
  window.history.replaceState(null, "", search ? `?${search}` : window.location.pathname);
}

export function OverviewView() {
  const searchParams = useSearchParams();
  const urlMarket = parseMarket(searchParams.get("market"));
  const urlPeriod = parsePeriod(searchParams.get("period"));

  const [market, setMarket] = useState(urlMarket);
  const [period, setPeriod] = useState(urlPeriod);
  const [synced, setSynced] = useState({ market: urlMarket, period: urlPeriod });
  if (synced.market !== urlMarket || synced.period !== urlPeriod) {
    // 網址被外部改變（例如點側欄連結回到預設頁面）時跟著更新
    setSynced({ market: urlMarket, period: urlPeriod });
    setMarket(urlMarket);
    setPeriod(urlPeriod);
  }

  const [view, setView] = useState<View>("cards");
  // 第一次切到某個市場才開始載入，減少外部 API 用量
  const [visited, setVisited] = useState<Set<Market>>(() => new Set([urlMarket]));
  if (!visited.has(market)) setVisited(new Set([...visited, market]));

  function selectMarket(position: number) {
    const next = MARKETS[position];
    setMarket(next);
    writeUrl(next, period);
  }

  function selectPeriod(value: string) {
    const next = value as Period;
    setPeriod(next);
    writeUrl(market, next);
  }

  const pages = MARKETS.map((item) => ({
    id: item,
    label: MARKET_LABEL[item],
    content: <MarketPanel market={item} period={period} view={view} enabled={visited.has(item)} />,
  }));
  const index = MARKETS.indexOf(market);

  return (
    <>
      <PageHeader
        title="大盤總覽"
        description="左右滑動或點選切換台股與美股，查看指數與市值前 12 大公司的走勢"
        actions={<MarketStatusPills />}
      />
      {/* 篩選列：市場、期間與顯示方式放在同一列，作用於下方所有內容 */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <PageToggle pages={pages} index={index} onChange={selectMarket} />
        <Tabs value={period} onValueChange={selectPeriod}>
          <TabsList aria-label="走勢期間">
            {PERIODS.map((item) => (
              <TabsTrigger key={item.value} value={item.value} className="px-2.5">
                {item.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <Tabs value={view} onValueChange={(value) => setView(value as View)} className="sm:ml-auto">
          <TabsList aria-label="顯示方式">
            <TabsTrigger value="cards">走勢卡片</TabsTrigger>
            <TabsTrigger value="table">表格</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      <MarketSlider pages={pages} index={index} onChange={selectMarket} />
    </>
  );
}

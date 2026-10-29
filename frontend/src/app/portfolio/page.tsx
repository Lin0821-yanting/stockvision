import type { Metadata } from "next";

import { PortfolioView } from "@/components/portfolio/portfolio-view";

export const metadata: Metadata = { title: "投資組合" };

export default function PortfolioPage() {
  return <PortfolioView />;
}

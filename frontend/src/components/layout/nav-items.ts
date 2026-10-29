import {
  ArrowLeftRight,
  BellRing,
  ChartCandlestick,
  GitCompareArrows,
  LayoutDashboard,
  Wallet,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "投資總覽", description: "Dashboard", icon: LayoutDashboard },
  { href: "/market", label: "股票看盤", description: "Market", icon: ChartCandlestick },
  { href: "/compare", label: "股票比較", description: "Compare", icon: GitCompareArrows },
  { href: "/trading", label: "模擬下單", description: "Trading", icon: ArrowLeftRight },
  { href: "/portfolio", label: "投資組合", description: "Portfolio", icon: Wallet },
  { href: "/alerts", label: "價格提醒", description: "Alerts", icon: BellRing },
];

export function isActivePath(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

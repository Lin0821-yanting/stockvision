import {
  ArrowLeftRight,
  BellRing,
  ChartCandlestick,
  GitCompareArrows,
  Globe,
  LayoutDashboard,
  Wallet,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
  /** 需要登入才能使用（未登入時側欄顯示鎖頭） */
  requiresAuth?: boolean;
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "投資總覽", description: "Dashboard", icon: LayoutDashboard },
  { href: "/overview", label: "大盤總覽", description: "Overview", icon: Globe },
  { href: "/market", label: "股票看盤", description: "Market", icon: ChartCandlestick },
  { href: "/compare", label: "股票比較", description: "Compare", icon: GitCompareArrows },
  { href: "/trading", label: "模擬下單", description: "Trading", icon: ArrowLeftRight, requiresAuth: true },
  { href: "/portfolio", label: "投資組合", description: "Portfolio", icon: Wallet, requiresAuth: true },
  { href: "/alerts", label: "價格提醒", description: "Alerts", icon: BellRing, requiresAuth: true },
];

export function isActivePath(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

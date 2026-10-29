import { GlobalSearch } from "./global-search";
import { MarketStatusPills } from "./market-status-pills";
import { MobileNav } from "./mobile-nav";
import { NotificationBell } from "./notification-bell";

export function Topbar() {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="mx-auto flex h-14 w-full max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
        <MobileNav />
        <GlobalSearch className="max-w-md flex-1" />
        <div className="ml-auto flex items-center gap-2">
          <MarketStatusPills className="hidden md:flex" />
          <NotificationBell />
        </div>
      </div>
    </header>
  );
}

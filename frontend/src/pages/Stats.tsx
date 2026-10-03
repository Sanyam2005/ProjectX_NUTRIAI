import { useLocation, useNavigate } from "react-router-dom";
import { BarChart3, CalendarDays } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { AnalyticsPage } from "@/pages/Analytics";
import { CalendarPage } from "@/pages/Calendar";
import { cx } from "@/lib/utils";

type Tab = "trends" | "calendar";

/** Single "Stats" hub hosting the Trends and Calendar views as tabs.
 *  Both /app/analytics and /app/calendar route here; the active tab is
 *  derived from the URL so back/forward and direct links Just Work.
 */
export function StatsPage() {
  const loc = useLocation();
  const nav = useNavigate();
  const tab: Tab = loc.pathname.endsWith("/calendar") ? "calendar" : "trends";

  return (
    <div className="pt-1 space-y-3">
      <PageHeader title="Stats" subtitle="Your trends and healthy days" />

      <div className="flex gap-2" role="tablist" aria-label="Stats sections">
        <TabButton
          active={tab === "trends"}
          onClick={() => nav("/app/analytics", { replace: true })}
          icon={<BarChart3 size={14} />}
        >
          Trends
        </TabButton>
        <TabButton
          active={tab === "calendar"}
          onClick={() => nav("/app/calendar", { replace: true })}
          icon={<CalendarDays size={14} />}
        >
          Calendar
        </TabButton>
      </div>

      {tab === "trends" ? <AnalyticsPage embedded /> : <CalendarPage embedded />}
    </div>
  );
}

function TabButton({
  active, onClick, icon, children,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <button
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition",
        active
          ? "bg-brand-500 text-white shadow-card"
          : "bg-white text-ink-muted hover:bg-surface-muted dark:bg-white/5 dark:text-white/70 dark:hover:bg-white/10",
      )}
    >
      {icon}
      {children}
    </button>
  );
}

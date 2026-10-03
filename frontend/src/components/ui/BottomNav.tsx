import { NavLink } from "react-router-dom";
import { Home, BarChart3, PlusCircle, History, User, Trophy } from "lucide-react";
import { cx } from "@/lib/utils";

const items = [
  { to: "/app",            label: "Home",      icon: Home },
  { to: "/app/history",    label: "History",   icon: History },
  { to: "/app/upload",     label: "Add",       icon: PlusCircle, primary: true },
  { to: "/app/analytics",  label: "Stats",     icon: BarChart3 },
  { to: "/app/challenges", label: "Compete",   icon: Trophy },
  { to: "/app/profile",    label: "Me",        icon: User },
];

export function BottomNav() {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-30 pb-[calc(env(safe-area-inset-bottom)+0.5rem)]"
      aria-label="Primary"
    >
      <div className="mx-auto max-w-md px-3">
        <div className="glass flex items-center justify-between rounded-3xl px-1.5 py-1.5">
          {items.map(({ to, label, icon: Icon, primary }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/app"}
              className={({ isActive }) =>
                cx(
                  "flex flex-1 flex-col items-center gap-0.5 rounded-2xl px-1 py-2 text-[10px] font-semibold transition",
                  primary
                    ? "text-white"
                    : isActive
                      ? "text-brand-600 dark:text-brand-300"
                      : "text-ink-subtle hover:text-ink dark:hover:text-white"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={cx(
                      "grid h-8 w-8 place-items-center rounded-xl transition",
                      primary
                        ? "h-9 w-9 bg-gradient-to-br from-brand-500 to-emerald-600 shadow-[0_10px_24px_-8px_rgba(16,185,129,.7)]"
                        : isActive
                          ? "bg-brand-50 dark:bg-brand-900/30"
                          : ""
                    )}
                  >
                    <Icon size={primary ? 22 : 18} strokeWidth={2.2} />
                  </span>
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}

import { ReactNode } from "react";
import { ChevronLeft } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

interface Props {
  title: string;
  subtitle?: string;
  back?: boolean | string;
  right?: ReactNode;
}

export function PageHeader({ title, subtitle, back = true, right }: Props) {
  const nav = useNavigate();
  const loc = useLocation();
  const showBack = back !== false && loc.pathname !== "/app";

  return (
    <header className="sticky top-0 z-20 -mx-4 mb-3 px-4 pt-[calc(env(safe-area-inset-top)+0.5rem)]">
      <div className="glass flex items-center gap-3 rounded-2xl px-3 py-2.5">
        {showBack ? (
          <button
            className="grid h-9 w-9 place-items-center rounded-xl text-ink-muted hover:bg-white/40 dark:hover:bg-white/5"
            onClick={() => (typeof back === "string" ? nav(back) : nav(-1))}
            aria-label="Back"
          >
            <ChevronLeft size={20} />
          </button>
        ) : (
          <div className="w-9" />
        )}
        <div className="flex-1 min-w-0">
          <h1 className="truncate font-display text-base font-bold leading-tight">{title}</h1>
          {subtitle && <p className="truncate text-xs text-ink-subtle">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-1">{right}</div>
      </div>
    </header>
  );
}

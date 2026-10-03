import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { getCalendar } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { cx, formatNumber } from "@/lib/utils";
import type { CalendarDay, DayStatus } from "@/types";

const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const STATUS_TONE: Record<DayStatus, string> = {
  ok:      "bg-brand-500 text-white",
  over:    "bg-rose-500 text-white",
  under:   "bg-amber-400 text-amber-900",
  empty:   "bg-surface-muted text-ink-subtle dark:bg-white/5",
  future:  "bg-transparent text-ink-subtle/60",
};

const STATUS_LABEL: Record<DayStatus, string> = {
  ok:     "On goal",
  over:   "Over goal",
  under:  "Under goal",
  empty:  "No meals logged",
  future: "Upcoming",
};

export function CalendarPage({ embedded = false }: { embedded?: boolean } = {}) {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [selected, setSelected] = useState<CalendarDay | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["calendar", year, month],
    queryFn: () => getCalendar(year, month),
  });

  function step(delta: number) {
    let m = month + delta;
    let y = year;
    if (m < 1) { m = 12; y -= 1; }
    if (m > 12) { m = 1; y += 1; }
    setYear(y);
    setMonth(m);
    setSelected(null);
  }

  // Build a fixed 6×7 grid starting on Monday.
  const grid = useMemo(() => {
    if (!data) return [];
    const cells: (CalendarDay | null)[] = [];
    for (let i = 0; i < data.first_weekday; i++) cells.push(null);
    for (const d of data.days) cells.push(d);
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [data]);

  return (
    <div className={embedded ? "space-y-4" : "pt-1 space-y-4"}>
      {!embedded && <PageHeader title="Calendar" subtitle="Healthy days at a glance" />}

      <Card>
        <div className="flex items-center justify-between">
          <button
            onClick={() => step(-1)}
            className="grid h-9 w-9 place-items-center rounded-xl text-ink-muted hover:bg-surface-muted dark:hover:bg-white/5"
            aria-label="Previous month"
          >
            <ChevronLeft size={18} />
          </button>
          <div className="font-display text-base font-bold">
            {MONTHS[month - 1]} {year}
          </div>
          <button
            onClick={() => step(1)}
            className="grid h-9 w-9 place-items-center rounded-xl text-ink-muted hover:bg-surface-muted dark:hover:bg-white/5"
            aria-label="Next month"
          >
            <ChevronRight size={18} />
          </button>
        </div>

        <div className="mt-3 grid grid-cols-7 gap-1 text-center text-[10px] font-semibold uppercase tracking-wider text-ink-subtle">
          {DOW.map((d) => (<div key={d}>{d}</div>))}
        </div>

        {isLoading || !data ? (
          <div className="mt-2 grid grid-cols-7 gap-1.5">
            {Array.from({ length: 42 }).map((_, i) => (
              <Skeleton key={i} className="aspect-square rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="mt-2 grid grid-cols-7 gap-1.5">
            {grid.map((d, i) => {
              if (d === null) return <div key={`b${i}`} className="aspect-square" />;
              const day = Number(d.date.slice(-2));
              const isToday = d.date === todayIso();
              const isSelected = selected?.date === d.date;
              return (
                <button
                  key={d.date}
                  onClick={() => setSelected(d)}
                  className={cx(
                    "relative aspect-square rounded-lg text-xs font-semibold transition",
                    STATUS_TONE[d.status],
                    isToday && "ring-2 ring-brand-500 ring-offset-2 ring-offset-white dark:ring-offset-[#15181d]",
                    isSelected && "scale-[1.04]",
                  )}
                  aria-label={`${d.date} — ${STATUS_LABEL[d.status]}`}
                >
                  <span className="absolute left-1 top-1 text-[10px] opacity-80">{day}</span>
                  {d.meal_count > 0 && (
                    <span className="absolute bottom-1 right-1 text-[9px] tabular-nums opacity-90">
                      {Math.round(d.calories)}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-2 text-[11px] text-ink-subtle">
          <Legend tone={STATUS_TONE.ok}    label="On goal" />
          <Legend tone={STATUS_TONE.over}  label="Over" />
          <Legend tone={STATUS_TONE.under} label="Under" />
          <Legend tone={STATUS_TONE.empty} label="Not logged" />
        </div>
      </Card>

      {/* Summary */}
      {data && (
        <Card>
          <h3 className="font-display text-base font-bold">This month</h3>
          <div className="mt-3 grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
            <Stat tone="bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300" label="Healthy" value={data.summary.healthy_days} />
            <Stat tone="bg-rose-50  text-rose-700  dark:bg-rose-500/10 dark:text-rose-300"   label="Over"    value={data.summary.over_days} />
            <Stat tone="bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300" label="Skipped" value={data.summary.skipped_days} />
            <Stat tone="bg-slate-50 text-slate-700 dark:bg-white/5    dark:text-white"       label="Logged"  value={data.summary.logged_days} />
          </div>
        </Card>
      )}

      {/* Selected day detail */}
      {selected && (
        <Card>
          <div className="flex items-baseline justify-between">
            <h3 className="font-display text-base font-bold">
              {new Date(selected.date).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}
            </h3>
            <span className={cx("chip", toneForStatus(selected.status))}>{STATUS_LABEL[selected.status]}</span>
          </div>
          {selected.meal_count === 0 ? (
            <p className="mt-2 text-sm text-ink-subtle">No meals logged on this day.</p>
          ) : (
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              <Box label="kcal"    value={`${formatNumber(selected.calories, 0)} / ${selected.target_calories}`} />
              <Box label="Protein" value={`${formatNumber(selected.protein_g, 0)} g`} />
              <Box label="Carbs"   value={`${formatNumber(selected.carbs_g, 0)} g`} />
              <Box label="Fat"     value={`${formatNumber(selected.fat_g, 0)} g`} />
              <Box label="Fiber"   value={`${formatNumber(selected.fiber_g, 0)} g`} />
              <Box label="Water"   value={`${formatNumber(selected.water_ml, 0)} ml`} />
              <Box label="Meals"   value={`${selected.meal_count}`} />
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function Legend({ tone, label }: { tone: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cx("h-3 w-3 rounded-sm", tone)} />
      {label}
    </span>
  );
}

function Stat({ tone, label, value }: { tone: string; label: string; value: number }) {
  return (
    <div className={cx("rounded-xl px-2 py-3", tone)}>
      <div className="font-display text-xl font-extrabold tabular-nums">{value}</div>
      <div className="text-[10px] uppercase tracking-wide">{label}</div>
    </div>
  );
}

function Box({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface-muted px-2 py-2 dark:bg-white/5">
      <div className="text-[10px] uppercase tracking-wide text-ink-subtle">{label}</div>
      <div className="font-display text-sm font-bold tabular-nums">{value}</div>
    </div>
  );
}

function todayIso(): string {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function toneForStatus(s: DayStatus): string {
  switch (s) {
    case "ok":    return "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300";
    case "over":  return "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300";
    case "under": return "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300";
    default:      return "";
  }
}

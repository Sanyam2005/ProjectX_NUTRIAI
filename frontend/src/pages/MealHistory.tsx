import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Filter, Search, Trash2 } from "lucide-react";

import { imageUrl } from "@/api/client";
import { deleteMeal, listMeals } from "@/api/nutriai";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { cx, formatNumber, formatTime, mealTypeIcon } from "@/lib/utils";
import type { Meal, MealType } from "@/types";

const FILTERS: Array<{ key: MealType | "all"; label: string }> = [
  { key: "all",       label: "All" },
  { key: "breakfast", label: "Breakfast" },
  { key: "lunch",     label: "Lunch" },
  { key: "dinner",    label: "Dinner" },
  { key: "snack",     label: "Snack" },
];

export function MealHistoryPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<MealType | "all">("all");
  const [q, setQ] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["meals", filter, q],
    queryFn: () =>
      listMeals({
        meal_type: filter === "all" ? undefined : filter,
        q: q || undefined,
        limit: 100,
      }),
  });

  const grouped = useMemo(() => groupByDay(data ?? []), [data]);

  const remove = useMutation({
    mutationFn: (id: string) => deleteMeal(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["meals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return (
    <div className="pt-1">
      <PageHeader title="Meal history" subtitle="Browse, search, filter" />

      <Card padded className="mb-3">
        <label className="relative block">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-subtle" />
          <input
            className="input pl-9"
            placeholder="Search meals or ingredients…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
        <div className="-mx-1 mt-3 flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={cx(
                "chip whitespace-nowrap",
                filter === f.key
                  ? "bg-brand-500 text-white dark:bg-brand-500"
                  : ""
              )}
            >
              <Filter size={12} className="opacity-70" /> {f.label}
            </button>
          ))}
        </div>
      </Card>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-2xl" />
          ))}
        </div>
      ) : grouped.length === 0 ? (
        <Card className="text-center text-sm text-ink-subtle">
          No meals match. Try clearing filters or snap your first meal.
        </Card>
      ) : (
        <div className="space-y-5">
          {grouped.map((g) => (
            <section key={g.day}>
              <div className="mb-2 flex items-baseline justify-between px-1">
                <h3 className="font-display text-sm font-bold uppercase tracking-wide text-ink-muted">
                  {g.dayLabel}
                </h3>
                <span className="text-xs text-ink-subtle">{Math.round(g.total)} kcal</span>
              </div>
              <Card padded={false} className="overflow-hidden">
                <ul className="divide-y divide-surface-ring/60 dark:divide-white/5">
                  {g.items.map((m) => (
                    <li key={m.id} className="flex items-center gap-3 p-3">
                      {m.image_url ? (
                        <img src={imageUrl(m.image_url)} alt="" className="h-14 w-14 rounded-xl object-cover" />
                      ) : (
                        <div className="grid h-14 w-14 place-items-center rounded-xl bg-brand-100 text-xl dark:bg-brand-900/30">
                          {mealTypeIcon(m.meal_type)}
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-semibold">{m.name}</div>
                        <div className="text-[11px] text-ink-subtle">
                          {m.meal_type} · {formatTime(m.consumed_at)} · {m.ingredients.length} items
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-display text-sm font-bold tabular-nums">
                          {formatNumber(m.calories, 0)}
                          <span className="ml-1 text-[10px] font-medium text-ink-subtle">kcal</span>
                        </div>
                        <button
                          onClick={() => remove.mutate(m.id)}
                          className="mt-1 grid h-7 w-7 place-items-center rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10"
                          aria-label="Delete"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </Card>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

function groupByDay(meals: Meal[]): Array<{ day: string; dayLabel: string; total: number; items: Meal[] }> {
  const map = new Map<string, Meal[]>();
  for (const m of meals) {
    const d = m.consumed_at.slice(0, 10);
    const arr = map.get(d) ?? [];
    arr.push(m);
    map.set(d, arr);
  }
  return Array.from(map.entries())
    .sort((a, b) => (a[0] < b[0] ? 1 : -1))
    .map(([day, items]) => ({
      day,
      dayLabel: labelFor(day),
      total: items.reduce((s, x) => s + x.calories, 0),
      items: items.sort((a, b) => (a.consumed_at < b.consumed_at ? 1 : -1)),
    }));
}

function labelFor(iso: string): string {
  const date = new Date(iso);
  const today = new Date();
  const ymd = (d: Date) => d.toISOString().slice(0, 10);
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (ymd(date) === ymd(today)) return "Today";
  if (ymd(date) === ymd(yesterday)) return "Yesterday";
  return date.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}
